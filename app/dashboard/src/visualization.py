import streamlit as st 
import numpy as np 
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import ListedColormap
import random
import cv2

class FragmentVisualizer:
    """
    A class to handle all fragment visualizations in the dashboard
    """
    def __init__(self, fragments, original_image):
        self.fragments = fragments
        
        # Convert original image to numpy array if it's not already
        if isinstance(original_image, Image.Image):
            self.img_array = np.array(original_image)
        else:
            self.img_array = np.array(Image.open(original_image))
            
        self.height, self.width = self.img_array.shape[:2]
        self.num_fragments = len(fragments)
        self.colors = self._generate_colors(self.num_fragments)
    
    def display_metrics(self, process_time):
        """Display key metrics about the fragments in a single row"""
        sizes = [
            fragment.get("real_size_cm", fragment.get("size_cm", 0.0))
            for fragment in self.fragments
        ]
        
        if not sizes:
            st.warning("No fragment size data available")
            return []
            
        min_size = min(sizes)
        avg_size = np.mean(sizes)
        max_size = max(sizes)

        # Create a metrics container with styling
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        
        # Create a single row for all metrics
        cols = st.columns(4)
        
        with cols[0]:
            st.metric("⏱️ Processing Time", f"{process_time:.2f} sec")
        with cols[1]:
            st.metric("🔢 Total Fragments", f"{self.num_fragments}")
        with cols[2]:
            st.metric("📏 Average Size", f"{avg_size:.2f} cm")
        with cols[3]:
            st.metric("📊 Size Range", f"{min_size:.2f} - {max_size:.2f} cm")
            
        st.markdown('</div>', unsafe_allow_html=True)

        return sizes
    
    def display_all_visualizations(self, process_time):
        """Display all visualizations in a tabbed interface"""
        # Display metrics in a single row
        sizes = self.display_metrics(process_time)
        
        if not self.fragments:
            return
            
        # Create tabs for different visualizations
        tab1, tab2, tab3 = st.tabs([
            "Fragment Detection", 
            "Size Distribution", 
            "Individual Fragments"
        ])
        
        with tab1:
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                # Combined masks visualization
                self.display_combined_masks()
                
            with col2:
                # Bounding boxes visualization
                self.display_bounding_boxes()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            # Size distribution section
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            from src.utils import get_size_metrics_table
            from src.charts import plot_cdf
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.dataframe(
                    get_size_metrics_table(sizes), 
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                if cdf_fig := plot_cdf(sizes):
                    st.pyplot(cdf_fig)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab3:
            # Individual fragment masks
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            self.display_fragment_masks()
    st.markdown('</div>', unsafe_allow_html=True)

    def display_bounding_boxes(self):
        """Display all fragment bounding boxes with size labels on a single image"""
        if not self.fragments:
            st.warning("No fragments to display")
            return

        # Create figure with appropriate size
        fig_width = 8
        fig_height = fig_width * (self.height / self.width)

        fig, ax = plt.subplots(figsize=(fig_width, fig_height))

        # Display original image
        ax.imshow(self.img_array)
        ax.set_title("Fragment Bounding Boxes")
        ax.axis('off')

        # Add bounding boxes and labels
        for i, fragment in enumerate(self.fragments):
            if bbox := fragment.get("bbox", None):
                x1, y1, x2, y2 = bbox
                width = x2 - x1
                height = y2 - y1

                # Create rectangle patch
                rect = patches.Rectangle(
                    (x1, y1), width, height, 
                    linewidth=2, 
                    edgecolor=self.colors[i], 
                    facecolor='none'
                )
                ax.add_patch(rect)

                # Add fragment ID and size text with background box
                text_y = y1 - 5

                # Handle text positioning for boxes near edges
                if text_y < 15:
                    text_y = y1 + height + 15



        # Adjust layout
        plt.tight_layout()

        # Display the figure
        st.pyplot(fig)

    def display_combined_masks(self):
        """Display all fragment masks combined on a single image with different colors"""
        if not self.fragments:
            st.warning("No fragments to display")
            return
        
        fig, ax = plt.subplots(figsize=(8, 8 * (self.height / self.width)))
        
        # Display original image
        ax.imshow(self.img_array)
        ax.set_title("Segmented Fragments")
        ax.axis('off')
        
        # Create an RGBA array for the colored overlay
        colored_overlay = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        
        # Process each fragment
        for i, fragment in enumerate(self.fragments):
            bbox = fragment.get("bbox", None)
            mask_data = fragment.get("mask_data", None)
            
            if bbox and mask_data:
                # Extract mask parameters
                x1, y1, x2, y2 = bbox
                mask_rle = mask_data.get("rle", [])
                mask_shape = mask_data.get("shape", [y2-y1, x2-x1])
                
                # Create binary mask from RLE
                cropped_mask = self._rle_to_binary_mask(mask_rle, mask_shape)
                
                # Create a full-size mask
                full_mask = np.zeros((self.height, self.width), dtype=np.uint8)
                
                # Place cropped mask into full mask at the correct position
                y2 = min(y1 + mask_shape[0], self.height)
                x2 = min(x1 + mask_shape[1], self.width)
                
                # Handle boundary cases
                mask_h = min(cropped_mask.shape[0], y2 - y1)
                mask_w = min(cropped_mask.shape[1], x2 - x1)
                full_mask[y1:y1+mask_h, x1:x1+mask_w] = cropped_mask[:mask_h, :mask_w]
                
                # Convert color from hex to rgba with alpha=0.5
                color_hex = self.colors[i]
                r = int(color_hex[1:3], 16)
                g = int(color_hex[3:5], 16)
                b = int(color_hex[5:7], 16)
                
                # Add this mask to the colored overlay
                colored_overlay[full_mask > 0] = [r, g, b, 128]  # Alpha=128 (50% transparency)
                
                # Add contour around the fragment
                contours, _ = cv2.findContours(full_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    ax.plot(contour[:, 0, 0], contour[:, 0, 1], color=color_hex, linewidth=1.5)
        
        # Display the colored mask overlay
        ax.imshow(colored_overlay, alpha=0.5)
        
        # Adjust layout
        plt.tight_layout()
        
        # Display the figure
        st.pyplot(fig)

    def display_fragment_masks(self):
        """Display individual fragment masks in a grid layout"""
        if not self.fragments:
            st.warning("No fragments to display")
            return

        # Determine grid layout based on number of fragments
        if self.num_fragments <= 3:
            cols = self.num_fragments
        elif self.num_fragments <= 8:
            cols = 4
        else:
            cols = 5

        # Create grid of columns for displaying masks
        mask_cols = st.columns(min(cols, self.num_fragments))

        for i, fragment in enumerate(self.fragments):
            col_idx = i % cols

            with mask_cols[col_idx]:
                # Get bounding box and mask data
                bbox = fragment.get("bbox", None)
                mask_data = fragment.get("mask_data", None)

                if bbox and mask_data:
                    # Extract mask parameters
                    x1, y1, x2, y2 = bbox
                    mask_rle = mask_data.get("rle", [])
                    mask_shape = mask_data.get("shape", [y2-y1, x2-x1])

                    # Create binary mask from RLE
                    mask = self._rle_to_binary_mask(mask_rle, mask_shape)

                    # Create visualization
                    fig, ax = plt.subplots(figsize=(3, 3))

                    # Create a cropped view of the original image
                    cropped_img = self.img_array[y1:y2, x1:x2]

                    # Apply the mask as an overlay
                    overlay = np.zeros_like(cropped_img)
                    if cropped_img.ndim == 3:  # Color image
                        overlay[:, :, 0] = mask * 255  # Red channel
                        overlay = overlay.astype(np.uint8)
                        alpha = 0.5
                        img_with_mask = cv2.addWeighted(cropped_img, 1, overlay, alpha, 0)
                        ax.imshow(img_with_mask)
                    else:  # Grayscale image
                        ax.imshow(cropped_img, cmap='gray')
                        ax.imshow(mask, alpha=0.5, cmap=ListedColormap(['none', self.colors[i]]))

                    # Remove axis labels
                    ax.set_xticks([])
                    ax.set_yticks([])

                    # Add fragment number and size
                    fragment_size = fragment.get("size_cm", 0)
                    ax.set_title(f"#{i+1}: {fragment_size:.1f} cm", fontsize=10)

                    st.pyplot(fig)
                    plt.close(fig)

                    if metrics := fragment.get("metrics", None):
                        metrics_html = f"""
                        <div class="fragment-metrics">
                            <span class="fragment-tag" style="background-color: {self.colors[i]}">#{i+1}</span>
                            <strong>Size:</strong> {fragment_size:.1f} cm<br>
                            <strong>Area:</strong> {metrics.get('area', 0):.1f} px²<br>
                            <strong>Perimeter:</strong> {metrics.get('perimeter', 0):.1f} px<br>
                            <strong>Circularity:</strong> {metrics.get('circularity', 0):.2f}
                        </div>
                        """
                        st.markdown(metrics_html, unsafe_allow_html=True)
                else:
                    st.write(f"Fragment #{i+1}")
                    st.write("No mask data available")
    
    def _generate_colors(self, n):
        """Generate n visually distinct colors"""
        colors = []
        for i in range(n):
            # Use HSV color space for better visual distinction
            hue = i / n
            saturation = 0.7 + random.random() * 0.3
            value = 0.7 + random.random() * 0.3
            
            # Convert HSV to RGB
            h = hue * 6
            c = value * saturation
            x = c * (1 - abs(h % 2 - 1))
            m = value - c
            
            if h < 1:
                r, g, b = c, x, 0
            elif h < 2:
                r, g, b = x, c, 0
            elif h < 3:
                r, g, b = 0, c, x
            elif h < 4:
                r, g, b = 0, x, c
            elif h < 5:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
            
            r, g, b = (r + m, g + m, b + m)
            colors.append(f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}')
        
        return colors
    
    def _rle_to_binary_mask(self, rle, shape):
        """Convert run-length encoding back to binary mask."""
        height, width = shape
        mask = np.zeros(height * width, dtype=np.uint8)
        
        for start, length in rle:
            if 0 <= start < len(mask) and length > 0:
                end = min(start + length, len(mask))
                mask[start:end] = 1
        
        return mask.reshape(height, width)

# For backward compatibility
def create_thumbnail(image_file, max_size=(100, 100)):
    """Create a thumbnail from an image file"""
    image = Image.open(image_file)
    image.thumbnail(max_size)
    return image

def size_status(fragments, data):
    """For backward compatibility"""
    visualizer = FragmentVisualizer(fragments, data['file'])
    return visualizer.display_metrics(data['process_time'])

def display_bounding_boxes(fragments, original_image):
    """For backward compatibility"""
    visualizer = FragmentVisualizer(fragments, original_image)
    return visualizer.display_bounding_boxes()

def display_combined_masks(fragments, original_image):
    """For backward compatibility"""
    visualizer = FragmentVisualizer(fragments, original_image)
    return visualizer.display_combined_masks()

def display_fragment_masks(fragments, original_image):
    """For backward compatibility"""
    visualizer = FragmentVisualizer(fragments, original_image)
    return visualizer.display_fragment_masks()