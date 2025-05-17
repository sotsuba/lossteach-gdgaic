import matplotlib.pyplot as plt
import numpy as np

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
