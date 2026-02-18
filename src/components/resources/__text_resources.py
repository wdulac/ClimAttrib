from utils.paths import RESOURCES

QUICKGUIDE_FILE = RESOURCES / 'quickguide.md'
with open(QUICKGUIDE_FILE, 'r', encoding='utf-8') as f:
    QUICKGUIDE_CONTENT = f.read()

INTERPRETATION_HELP_FILE = RESOURCES / 'interpretation_help.md'
with open(INTERPRETATION_HELP_FILE, 'r') as f:
    INTERPRETATION_HELP_CONTENT = f.read()

DISCLAIMER_FILE = RESOURCES / 'disclaimer.md'
with open(DISCLAIMER_FILE, 'r', encoding='utf-8') as f:
    DISCLAIMER_CONTENT = f.read()

COMPUTE_TOOLTIP_MD_FILE = RESOURCES / 'compute_tooltip_content_usecase.md'
with open(COMPUTE_TOOLTIP_MD_FILE, 'r', encoding='utf-8') as f:
    COMPUTE_TOOLTIP_CONTENT = f.read()

ANOMALY_HELP_MD_FILE = RESOURCES / 'anomaly_tooltip_content.md'
with open(ANOMALY_HELP_MD_FILE, 'r', encoding='utf-8') as f:
    ANOMALY_TOOLTIP_CONTENT = f.read()

CLIMATOLOGY_HELP_MD_FILE = RESOURCES / 'climatology_tooltip_content.md'
with open(CLIMATOLOGY_HELP_MD_FILE, 'r', encoding='utf-8') as f:
    CLIMATOLOGY_TOOLTIP_CONTENT = f.read()