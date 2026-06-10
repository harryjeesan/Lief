def get_simplified_dom(page) -> str:
    """
    Extract visible interactive elements from the page and format as a simplified list.
    Also extracts page title to give the model context.
    """
    try:
        # Get page title
        title = page.title()
        
        # Find all potentially interactive elements
        elements = page.locator("button, input, select, textarea, a, [role='button'], [role='checkbox'], [role='radio']").all()
        lines = []
        lines.append(f"Page Title: {title}\n")
        lines.append("Interactive Elements:")
        
        for i, el in enumerate(elements):
            try:
                if not el.is_visible():
                    continue
                
                tag = el.evaluate("el => el.tagName.toLowerCase()")
                text = (el.text_content() or "").strip()
                
                # Clean up whitespace and restrict length
                text = " ".join(text.split())
                if len(text) > 60:
                    text = text[:57] + "..."
                    
                attrs = []
                
                # Retrieve key attributes
                for attr in ["id", "name", "placeholder", "aria-label", "role", "href", "type"]:
                    val = el.get_attribute(attr)
                    if val:
                        attrs.append(f'{attr}="{val}"')
                
                attr_str = " " + " ".join(attrs) if attrs else ""
                text_str = f' text="{text}"' if text else ""
                
                lines.append(f'[{i}] <{tag}{attr_str}{text_str}>')
            except Exception:
                continue # Skip elements that might have become detached
            
        if len(lines) <= 2:
            lines.append("(No visible interactive elements found)")
            
        return "\n".join(lines)
    except Exception as e:
        return f"Error extracting simplified DOM: {e}"
