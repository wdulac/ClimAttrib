import re
import dash_mantine_components as dmc

# Regex for parsing token in the form of [[CI:<label>|<display>]]
TOKEN_RE = re.compile(r"\[\[CI:(?P<label>[^|\]]+)\|(?P<display>[^\]]+)\]\]")


def render_text_with_tooltips(paragraph: str) -> dmc.Text:
    """
    Renders a text string into Dash web elements, using dmc.Tooltips to show confidence intervals as tooltips.
    Tooltips content (i.e label) are extracted from tokens using regex.

    :paragraph: String outputed by jinja2 (template rendering)
    """

    children = [] # Children for the resulting dmc.Text
    pos = 0
    for match in TOKEN_RE.finditer(paragraph):
        if match.start() > pos:
            # Text between the start of paragraph and the start of our first token.
            before = paragraph[pos:match.start()] # Text before a CI token
            children.append(before)
        ## Handle the token
        # Separate label and value to display from the token
        label = match.group('label')
        display = match.group('display')
        # Create a tooltip element from them
        children.append(
            dmc.Tooltip(
                label=label,
                withArrow=True,
                position="top",
                children=dmc.Text(display, span=True, fw=700),
                boxWrapperProps={
                    "className": "ci", # Styling in assets/components/confidence_tooltips.css
                    "style": {"display": "inline-block"}
                    }
            )
        )
        pos = match.end() # Update position to the end of this token

    if pos < len(paragraph):
        # Residual text between last token and end of paragraph.
        children.append(paragraph[pos:])

    # Don't use span on the main element to get an actual paragraph
    return dmc.Text(children, span=False, style={"margin-block": "18px"}) # Use same margin as dcc.Markdown