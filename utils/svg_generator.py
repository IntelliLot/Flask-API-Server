"""
SVG Generator for parking slot visualization
"""

from typing import List, Tuple


def generate_svg(parking_rectangles: List[Tuple[int, int, int, int]],
                occupancy: List[bool],
                image_width: int,
                image_height: int) -> str:
    """
    Generate SVG visualization of parking slots
    
    Args:
        parking_rectangles: List of (x1, y1, x2, y2) tuples
        occupancy: List of boolean values (True = occupied, False = empty)
        image_width: Image width in pixels
        image_height: Image height in pixels
    
    Returns:
        SVG code as string
    """
    svg_parts = []
    
    # SVG header
    svg_parts.append(f'<svg width="{image_width}" height="{image_height}" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append(f'<rect width="{image_width}" height="{image_height}" fill="none"/>')
    
    # Draw each parking slot
    for i, (rect, is_occupied) in enumerate(zip(parking_rectangles, occupancy), 1):
        x1, y1, x2, y2 = rect
        width = x2 - x1
        height = y2 - y1
        
        # Choose color based on occupancy
        if is_occupied:
            fill_color = "rgba(255, 0, 0, 0.3)"  # Red with transparency
            stroke_color = "#FF0000"
            status = "Occupied"
        else:
            fill_color = "rgba(0, 255, 0, 0.3)"  # Green with transparency
            stroke_color = "#00FF00"
            status = "Empty"
        
        # Draw rectangle
        svg_parts.append(f'<rect x="{x1}" y="{y1}" width="{width}" height="{height}" ')
        svg_parts.append(f'fill="{fill_color}" stroke="{stroke_color}" stroke-width="3" ')
        svg_parts.append(f'data-slot="{i}" data-status="{status}"/>')
        
        # Add slot number text
        text_x = x1 + width // 2
        text_y = y1 + height // 2
        font_size = min(width, height) // 3
        font_size = max(12, min(font_size, 24))
        
        svg_parts.append(f'<text x="{text_x}" y="{text_y}" ')
        svg_parts.append(f'font-family="Arial, sans-serif" font-size="{font_size}" ')
        svg_parts.append(f'font-weight="bold" fill="white" text-anchor="middle" ')
        svg_parts.append(f'dominant-baseline="middle" ')
        svg_parts.append(f'stroke="black" stroke-width="1">{i}</text>')
    
    svg_parts.append('</svg>')
    
    return ''.join(svg_parts)


def generate_slot_details(parking_rectangles: List[Tuple[int, int, int, int]],
                         occupancy: List[bool]) -> List[dict]:
    """
    Generate detailed information for each parking slot
    
    Args:
        parking_rectangles: List of (x1, y1, x2, y2) tuples
        occupancy: List of boolean values
    
    Returns:
        List of slot detail dictionaries
    """
    slots_details = []
    
    for i, (rect, is_occupied) in enumerate(zip(parking_rectangles, occupancy), 1):
        x1, y1, x2, y2 = rect
        
        slot_info = {
            'slot_number': i,
            'rectangle': {
                'x1': int(x1),
                'y1': int(y1),
                'x2': int(x2),
                'y2': int(y2)
            },
            'dimensions': {
                'width': int(x2 - x1),
                'height': int(y2 - y1)
            },
            'occupied': bool(is_occupied),
            'status': 'OCCUPIED' if is_occupied else 'EMPTY'
        }
        
        slots_details.append(slot_info)
    
    return slots_details
