from app_platform.shared.paths import MARKDOWN_RESOURCES

QUICKGUIDE_FILE = MARKDOWN_RESOURCES / 'quickguide.md'
with open(QUICKGUIDE_FILE, 'r', encoding='utf-8') as f:
    QUICKGUIDE_CONTENT = f.read()

INTERPRETATION_HELP_FILE = MARKDOWN_RESOURCES / 'interpretation_help.md'
with open(INTERPRETATION_HELP_FILE, 'r') as f:
    INTERPRETATION_HELP_CONTENT = f.read()

DISCLAIMER_FILE = MARKDOWN_RESOURCES / 'disclaimer.md'
with open(DISCLAIMER_FILE, 'r', encoding='utf-8') as f:
    DISCLAIMER_CONTENT = f.read()

ABOUT_FILE = MARKDOWN_RESOURCES / 'about.md'
with open(ABOUT_FILE, 'r', encoding='utf-8') as f:
    ABOUT_CONTENT = f.read()

COMPUTE_TOOLTIP_MD_FILE = MARKDOWN_RESOURCES / 'compute_tooltip_content_usecase.md'
with open(COMPUTE_TOOLTIP_MD_FILE, 'r', encoding='utf-8') as f:
    COMPUTE_TOOLTIP_CONTENT = f.read()

ANOMALY_HELP_MD_FILE = MARKDOWN_RESOURCES / 'anomaly_tooltip_content.md'
with open(ANOMALY_HELP_MD_FILE, 'r', encoding='utf-8') as f:
    ANOMALY_TOOLTIP_CONTENT = f.read()

CLIMATOLOGY_HELP_MD_FILE = MARKDOWN_RESOURCES / 'climatology_tooltip_content.md'
with open(CLIMATOLOGY_HELP_MD_FILE, 'r', encoding='utf-8') as f:
    CLIMATOLOGY_TOOLTIP_CONTENT = f.read()