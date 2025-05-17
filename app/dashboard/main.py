import streamlit as st 
st.set_page_config(
    page_title="Fragment Detection Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

import requests
import logging
import src.config as config
import os
from requests.exceptions import RequestException, ConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential

from src.visualization import FragmentVisualizer, create_thumbnail
from src.utils import process_image
from src.helpers import check_api_health

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load custom CSS
def load_css():
    css_file = os.path.join(os.path.dirname(__file__), "src", "style.css")
    try:
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception as e:
        logger.error(f"Failed to load CSS: {str(e)}")

class DashboardApp:
    """Main dashboard application class"""
    def __init__(self):
        self.initialize_session_state()
        self.check_api_status()
        load_css()  # Load custom styles
        
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'processed_images' not in st.session_state:
            st.session_state.processed_images = {}
        if 'total_time' not in st.session_state:
            st.session_state.total_time = 0
        if 'selected_image' not in st.session_state:
            st.session_state.selected_image = None
        if 'api_retry_count' not in st.session_state:
            st.session_state.api_retry_count = 0
            
    def check_api_status(self):
        """Check if the API is available"""
        try:
            self.api_healthy = check_api_health()
        except Exception as e:
            self.api_healthy = False
            logger.error(f"Failed to check API health: {str(e)}")
    
    def run(self):
        """Run the main dashboard application"""
        st.title("Rock Fragment Detection Dashboard 🔍")
        
        if not self.api_healthy:
            st.error("⚠️ Model API is not available. Please check the backend service.")
            return
            
        # Set up the sidebar
        with st.sidebar:
            self.display_sidebar()
            
        # Main content area
        if st.session_state.selected_image:
            self.show_analysis(st.session_state.processed_images[st.session_state.selected_image])
        else:
            self.show_welcome_message()
            
    def show_welcome_message(self):
        """Display welcome message when no image is selected"""
        st.markdown("""
        <div class="welcome-container">
            <h3>👋 Welcome to the Rock Fragment Detection Dashboard!</h3>
            <p>This tool helps you analyze rock fragments in images using a machine learning model.</p>
            <p>Get started by:</p>
            <ol>
                <li>Upload images using the sidebar (up to 10 images)</li>
                <li>Adjust the detection threshold if needed</li>
                <li>Select an image from the sidebar to view its analysis</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
        # Show sample images if available
        if st.session_state.processed_images:
            st.markdown("### 🖼️ Your uploaded images")
            cols = st.columns(4)
            for i, (filename, data) in enumerate(list(st.session_state.processed_images.items())[:4]):
                with cols[i % 4]:
                    st.image(data['file'], use_container_width=True, caption=filename)
                    if st.button(f"Select {filename}", key=f"welcome_{filename}"):
                        st.session_state.selected_image = filename
                        st.rerun()
    
    @retry(
        stop=stop_after_attempt(config.MAX_RETRIES),
        wait=wait_exponential(multiplier=config.INITIAL_RETRY_DELAY),
        reraise=True
    )
    def show_analysis(self, data):
        """Display the analysis of the selected image"""
        if not data:
            st.info("👈 Select an image from the sidebar to view its analysis")
            return

        fragments = data['fragments']
        if not fragments:
            st.warning("⚠️ No fragments detected in this image. Try adjusting the threshold.")
            return

        # Display original image at the top
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.image(data['file'], use_container_width=True, caption="Original Image")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Use the new FragmentVisualizer class for all visualizations
        visualizer = FragmentVisualizer(fragments, data['file'])
        visualizer.display_all_visualizations(data['process_time'])
    
    def display_sidebar(self):
        """Display the sidebar with controls and settings"""
        st.header("📊 Controls & Settings")

        # File upload section
        self.handle_file_upload()
        
        # Image selection
        if st.session_state.processed_images:
            self.display_image_selector()
            
        # Performance metrics
        if st.session_state.processed_images:
            st.markdown("---")
            st.subheader("⚡ Performance")
            current_file_count = len(st.session_state.processed_images)
            st.metric("Total Processing Time", f"{st.session_state.total_time:.2f} sec")
            st.metric("Processed Images", f"{current_file_count}/{config.MAX_FILES}")
            
    def handle_file_upload(self):
        """Handle file upload section in the sidebar"""
        st.subheader("📁 Upload Images")
        current_file_count = len(st.session_state.processed_images)
        remaining_slots = config.MAX_FILES - current_file_count

        # Detection threshold slider
        score_threshold = st.slider(
            'Detection Threshold',
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.05,
            help="Adjust the confidence threshold for fragment detection"
        )

        if remaining_slots > 0:
            st.info(f"You can upload up to {remaining_slots} more image(s)")

            uploaded_files = st.file_uploader(
                "Choose images",
                type=config.SUPPORTED_FORMATS,
                accept_multiple_files=True,
                help=f"Upload up to {config.MAX_FILES} images (Supported formats: {', '.join(config.SUPPORTED_FORMATS)})"
            )

            if uploaded_files and len(uploaded_files) + current_file_count > config.MAX_FILES:
                st.warning(f"⚠️ Only the first {remaining_slots} files will be processed.")
                uploaded_files = uploaded_files[:remaining_slots]
                
            # Process uploaded files
            if uploaded_files:
                with st.spinner("Processing images..."):
                    self.process_uploaded_files(uploaded_files, score_threshold)
        else:
            st.error("Maximum file limit reached (10 files)")
            
    def process_uploaded_files(self, uploaded_files, score_threshold):
        """Process uploaded files and store results in session state"""
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
                    
    def display_image_selector(self):
        """Display the image selector in the sidebar"""
        st.markdown("---")
        st.subheader("🖼️ Select Image")

        # Use a grid for selection
        for filename, data in st.session_state.processed_images.items():
            st.markdown('<div class="thumbnail-container">', unsafe_allow_html=True)
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
            st.markdown('</div>', unsafe_allow_html=True)
                    
        # Clear all button 
        if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
            st.session_state.processed_images = {}
            st.session_state.total_time = 0
            st.session_state.selected_image = None
            st.rerun()

if __name__ == "__main__":
    app = DashboardApp()
    app.run()