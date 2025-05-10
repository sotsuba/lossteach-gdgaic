import streamlit as st 
import requests
import matplotlib.pyplot as plt
import numpy as np 
from PIL import Image
import pandas as pd
import logging
import time
import os
from requests.exceptions import RequestException, ConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
API_URL = os.getenv("MODEL_API_URL", "http://localhost:8013") + "/predict"
API_HEALTH_URL = os.getenv("MODEL_API_URL", "http://localhost:8013") + "/health"
MAX_FILES = 10
SUPPORTED_FORMATS = ["jpg", "jpeg", "png"]
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds

# Set page config
st.set_page_config(
    page_title="Fragment Detection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
# st.markdown("""
#     <style>
#     .main {
#         padding: 2rem;
#     }
#     .stMetric {
#         background-color: #f0f2f6;
#         padding: 10px;
#         border-radius: 5px;
#         box-shadow: 0 1px 3px rgba(0,0,0,0.1);
#     }
#     .image-select {
#         padding: 8px;
#         border-radius: 4px;
#         border: 1px solid #ddd;
#         margin: 4px 0;
#         cursor: pointer;
#     }
#     .image-select:hover {
#         background-color: #f0f2f6;
#         border-color: #0066cc;
#     }
#     .image-select.selected {
#         background-color: #e6f3ff;
#         border-color: #0066cc;
#     }
#     .info-box {
#         background-color: #f8f9fa;
#         border-left: 4px solid #0066cc;
#         padding: 1em;
#         margin: 1em 0;
#         border-radius: 4px;
#     }
#     .error-box {
#         background-color: #fff3f3;
#         border-left: 4px solid #ff4b4b;
#         padding: 1em;
#         margin: 1em 0;
#         border-radius: 4px;
#     }
#     .success-box {
#         background-color: #f0fff4;
#         border-left: 4px solid #00cc66;
#         padding: 1em;
#         margin: 1em 0;
#         border-radius: 4px;
#     }
#     .metric-grid {
#         display: grid;
#         grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
#         gap: 1rem;
#         margin: 1rem 0;
#     }
#     </style>
#     """, unsafe_allow_html=True)

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY),
    reraise=True
)
def check_api_health():
    """Check if the model API is healthy with retry logic"""
    try:
        response = requests.get(API_HEALTH_URL, timeout=5)
        if response.status_code == 200:
            return True
        logger.error(f"API health check failed with status code: {response.status_code}")
        return False
    except RequestException as e:
        logger.error(f"API health check failed: {str(e)}")
        raise

@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=INITIAL_RETRY_DELAY),
    reraise=True
)
def process_image(image_file, score_threshold=0.5):
    """Process the image through the API with retry logic"""
    try:
        # Check API health first
        if not check_api_health():
            raise ConnectionError("Model API is not available. Please try again later.")

        start_time = time.time()
        files = {"file": (image_file.name, image_file.getvalue())}
        params = {"score_threshold": score_threshold}
        
        response = requests.post(API_URL, files=files, params=params, timeout=30)
        process_time = time.time() - start_time
        
        if response.status_code != 200:
            error_msg = response.json().get('detail', 'Unknown error')
            if "numpy" in error_msg.lower() and "version" in error_msg.lower():
                raise ConnectionError(
                    "Model API is experiencing compatibility issues with NumPy. "
                    "Please contact support for assistance."
                )
            if "segmentation fault" in error_msg.lower():
                raise ConnectionError("Model API crashed. Please try again later.")
            raise Exception(f"API Error: {error_msg}")
            
        return response, process_time
    except RequestException as e:
        logger.error(f"Error processing image: {str(e)}")
        raise ConnectionError(f"Failed to connect to Model API: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise

def plot_cdf(sizes, title="Cumulative Size Distribution"):
    """Create Cumulative Distribution Function plot for fragment sizes"""
    if not sizes:
        return None
    
    cnt_rocks = len(sizes)
    d_min, d_ave, d_max = np.min(sizes), np.average(sizes), np.max(sizes)
    d_10, d_50, d_90 = np.percentile(sizes, [10, 50, 90])
    
    sizes_with_zero = sizes.copy()
    sizes_with_zero.append(0.0)
    sizes_with_zero.sort()
    
    # Set style
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('white')
    
    # Plot CDF
    ax.plot(sizes_with_zero, np.arange(0, cnt_rocks + 1) / cnt_rocks * 100, 
           color='#0066cc', marker='o', label='CDF')
    
    # Plot vertical lines for statistics
    for value, color, label in [
        (d_min, '#28a745', f'Min: {d_min:.2f}cm'),
        (d_ave, '#fd7e14', f'Avg: {d_ave:.2f}cm'),
        (d_max, '#dc3545', f'Max: {d_max:.2f}cm'),
        (d_10, '#17a2b8', f'D10: {d_10:.2f}cm'),
        (d_50, '#6f42c1', f'D50: {d_50:.2f}cm'),
        (d_90, '#0066cc', f'D90: {d_90:.2f}cm')
    ]:
        ax.axvline(x=value, color=color, linestyle='--', label=label)
    
    ax.set_xlabel('Fragment Size (cm)')
    ax.set_ylabel('Cumulative Percentage (%)')
    ax.set_title(title)
    ax.set_xlim(0, d_max * 1.1)
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', framealpha=0.9)
    
    return fig

def get_size_metrics_table(sizes):
    """Create a size metrics table for display"""
    data = {
        'Percentile': ['10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'],
        'Size (cm)': [np.percentile(sizes, p) for p in range(10, 101, 10)]
    }
    return pd.DataFrame(data)

def create_thumbnail(image_file, max_size=(100, 100)):
    """Create a thumbnail from an image file"""
    image = Image.open(image_file)
    image.thumbnail(max_size)
    return image

def show_analysis(data):
    """Display the analysis of the selected image"""
    if not data:
        st.info("👈 Select an image from the sidebar to view its analysis")
        return

    fragments = data['fragments']
    if not fragments:
        st.warning("⚠️ No fragments detected in this image. Try adjusting the threshold.")
        return

    # Display original image and basic metrics
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.image(data['file'], use_container_width=True)
    
    with col2:
        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        sizes = [fragment.get("real_size_cm", fragment.get("size_cm", 0.0)) for fragment in fragments]
        total_fragments = len(fragments)
        min_size = min(sizes)
        avg_size = np.mean(sizes)
        max_size = max(sizes)
        
        st.metric("⏱️ Processing Time", f"{data['process_time']:.2f} sec")
        st.metric("🔢 Total Fragments", f"{total_fragments}")
        st.metric("📏 Average Size", f"{avg_size:.2f} cm")
        st.metric("📊 Size Range", f"{min_size:.2f} - {max_size:.2f} cm")
        st.markdown('</div>', unsafe_allow_html=True)

    # Size distribution and plot
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("### 📊 Size Distribution")
        st.dataframe(get_size_metrics_table(sizes), 
                    use_container_width=True,
                    hide_index=True)
    
    with col4:
        st.markdown("### 📈 Size Distribution Plot")
        cdf_fig = plot_cdf(sizes)
        if cdf_fig:
            st.pyplot(cdf_fig)

def main():
    st.title("Fragment Detection Dashboard 🔍")
    
    # Check API health at startup with retry
    try:
        api_healthy = check_api_health()
    except Exception as e:
        api_healthy = False
        logger.error(f"Failed to check API health after {MAX_RETRIES} attempts: {str(e)}")
    
    if not api_healthy:
        st.error("""
        <div class="error-box">
        <h3>⚠️ Model API is not available</h3>
        <p>The model API service appears to be down. This could be due to:</p>
        <ul>
            <li>NumPy version compatibility issues</li>
            <li>The model API service is not running</li>
            <li>Network connectivity problems</li>
        </ul>
        <p>Please ensure:</p>
        <ul>
            <li>The model API service is running</li>
            <li>You can access the API at: {API_URL}</li>
            <li>Check the API logs for any errors</li>
            <li>Try refreshing the page in a few moments</li>
        </ul>
        <p>If the problem persists, please contact support with the following information:</p>
        <ul>
            <li>Error message: {error}</li>
            <li>API URL: {API_URL}</li>
            <li>Time of error: {time}</li>
        </ul>
        </div>
        """.format(
            API_URL=API_URL,
            error=str(e) if 'e' in locals() else "Unknown error",
            time=time.strftime("%Y-%m-%d %H:%M:%S")
        ), unsafe_allow_html=True)
        return

    # Session state initialization
    if 'processed_images' not in st.session_state:
        st.session_state.processed_images = {}
    if 'total_time' not in st.session_state:
        st.session_state.total_time = 0
    if 'selected_image' not in st.session_state:
        st.session_state.selected_image = None
    if 'api_retry_count' not in st.session_state:
        st.session_state.api_retry_count = 0

    # Sidebar
    with st.sidebar:
        st.header("📊 Controls & Settings")
        
        # API Status with retry count
        try:
            api_healthy = check_api_health()
            if api_healthy:
                st.success("✅ Model API is healthy")
                st.session_state.api_retry_count = 0
            else:
                st.error("❌ Model API is not responding")
        except Exception as e:
            st.error(f"❌ Model API error: {str(e)}")
            st.session_state.api_retry_count += 1
            if st.session_state.api_retry_count >= MAX_RETRIES:
                st.error("""
                <div class="error-box">
                <h4>Maximum retry attempts reached</h4>
                <p>Please try the following:</p>
                <ol>
                    <li>Refresh the page</li>
                    <li>Check if the model API service is running</li>
                    <li>Contact support if the issue persists</li>
                </ol>
                </div>
                """, unsafe_allow_html=True)
        
        # File upload section
        st.subheader("📁 Upload Images")
        current_file_count = len(st.session_state.processed_images)
        remaining_slots = MAX_FILES - current_file_count
        
        if remaining_slots > 0:
            st.info(f"You can upload up to {remaining_slots} more image(s)")
            
            uploaded_files = st.file_uploader(
                "Choose images",
                type=SUPPORTED_FORMATS,
                accept_multiple_files=True,
                help=f"Upload up to {MAX_FILES} images (Supported formats: {', '.join(SUPPORTED_FORMATS)})"
            )
            
            if uploaded_files and len(uploaded_files) + current_file_count > MAX_FILES:
                st.warning(f"⚠️ Only the first {remaining_slots} files will be processed.")
                uploaded_files = uploaded_files[:remaining_slots]
        else:
            st.error("Maximum file limit reached (10 files)")
            uploaded_files = None
        
        # Detection threshold
        st.subheader("⚙️ Settings")
        score_threshold = st.slider(
            'Detection Threshold',
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Adjust the confidence threshold for fragment detection"
        )
        
        # Process new images
        if uploaded_files:
            with st.spinner("Processing images..."):
                for uploaded_file in uploaded_files:
                    if uploaded_file.name not in st.session_state.processed_images:
                        try:
                            response, process_time = process_image(uploaded_file, score_threshold)
                            data = response.json()
                            fragments = data.get("fragments", [])
                            st.session_state.processed_images[uploaded_file.name] = {
                                'file': uploaded_file,
                                'fragments': fragments,
                                'process_time': process_time
                            }
                            st.session_state.total_time += process_time
                            st.success(f"✅ Processed {uploaded_file.name}")
                        except ConnectionError as e:
                            st.error(f"❌ Connection Error: {str(e)}")
                            logger.error(f"Connection error details: {str(e)}", exc_info=True)
                        except Exception as e:
                            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
                            logger.error(f"Error details: {str(e)}", exc_info=True)
        
        # Image selection
        if st.session_state.processed_images:
            st.markdown("---")
            st.subheader("🖼️ Select Image")
            
            for filename, data in st.session_state.processed_images.items():
                col1, col2 = st.columns([1, 3])
                with col1:
                    thumbnail = create_thumbnail(data['file'])
                    st.image(thumbnail, width=50)
                with col2:
                    if st.button(
                        f"{filename}\n{len(data['fragments'])} fragments",
                        key=f"select_{filename}",
                        use_container_width=True,
                    ):
                        st.session_state.selected_image = filename
            
            # Clear all button
            st.markdown("---")
            if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
                st.session_state.processed_images = {}
                st.session_state.total_time = 0
                st.session_state.selected_image = None
                st.rerun()
        
        # Performance metrics
        if st.session_state.processed_images:
            st.markdown("---")
            st.subheader("⚡ Performance")
            st.metric("Total Processing Time", f"{st.session_state.total_time:.2f} sec")
            st.metric("Processed Images", f"{current_file_count}/{MAX_FILES}")
    
    # Main content - Analysis
    if st.session_state.selected_image:
        show_analysis(st.session_state.processed_images[st.session_state.selected_image])
    else:
        st.markdown("""
        <div class="info-box">
        <h3>👋 Welcome to the Fragment Detection Dashboard!</h3>
        <p>Get started by:</p>
        <ol>
            <li>Upload images using the sidebar (up to 10 images)</li>
            <li>Adjust the detection threshold if needed</li>
            <li>Select an image from the sidebar to view its analysis</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()