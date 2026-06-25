import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def generate_invoice(sale_id, customer_name, cart_items, total_amount, output_dir="assets/invoices"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    filename = f"Invoice_{sale_id}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1 * inch, height - 1 * inch, "OmniTrade AI")
    c.setFont("Helvetica", 12)
    c.drawString(1 * inch, height - 1.3 * inch, "Official Sales Receipt")
    
    c.drawString(1 * inch, height - 1.7 * inch, f"Invoice #: {sale_id}")
    c.drawString(1 * inch, height - 1.9 * inch, f"Customer: {customer_name if customer_name else 'Walk-in'}")
    
    # Table Header
    y = height - 2.5 * inch
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1 * inch, y, "Item")
    c.drawString(3.5 * inch, y, "Qty")
    c.drawString(4.5 * inch, y, "Price")
    c.drawString(5.5 * inch, y, "Total")
    
    c.line(1 * inch, y - 0.1 * inch, 6.5 * inch, y - 0.1 * inch)
    
    # Items
    y -= 0.4 * inch
    c.setFont("Helvetica", 12)
    for item in cart_items:
        line_total = item['quantity'] * item['price']
        c.drawString(1 * inch, y, item['name'][:30])
        c.drawString(3.5 * inch, y, str(item['quantity']))
        c.drawString(4.5 * inch, y, f"${item['price']:.2f}")
        c.drawString(5.5 * inch, y, f"${line_total:.2f}")
        y -= 0.3 * inch
        
    c.line(1 * inch, y + 0.1 * inch, 6.5 * inch, y + 0.1 * inch)
    
    # Total
    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(4.5 * inch, y, "Grand Total:")
    c.drawString(5.5 * inch, y, f"${total_amount:.2f}")
    
    c.save()
    return filepath
