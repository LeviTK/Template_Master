import os
from calibre.utils.config import JSONConfig, config_dir

# Persist the plugin settings
prefs = JSONConfig('plugins/epub_template_master')

# Default settings
prefs.defaults['templates'] = []  # List of {'name': str, 'filename': str}
prefs.defaults['default_template'] = ''  # filename of default template
prefs.defaults['duplicate_all_formats'] = False  # True=all formats, False=EPUB only

def get_template_dir():
    """Get the directory where templates are stored."""
    tpl_dir = os.path.join(config_dir, 'plugins', 'epub_template_master_templates')
    if not os.path.exists(tpl_dir):
        os.makedirs(tpl_dir)
    return tpl_dir

def get_templates():
    """Get list of templates."""
    return prefs['templates']

def set_templates(templates):
    """Set the template list."""
    prefs['templates'] = templates

def get_default_template():
    """Get the default template filename."""
    return prefs['default_template']

def set_default_template(filename):
    """Set the default template."""
    prefs['default_template'] = filename

def add_template(name, filename):
    """Add a template to the list."""
    templates = get_templates()
    templates.append({'name': name, 'filename': filename})
    set_templates(templates)

def remove_template(filename):
    """Remove a template from the list."""
    templates = get_templates()
    templates = [t for t in templates if t['filename'] != filename]
    set_templates(templates)
    if get_default_template() == filename:
        set_default_template('')

def get_template_path(filename):
    """Get full path for a template file."""
    return os.path.join(get_template_dir(), filename)

def get_duplicate_all_formats():
    """Get whether to duplicate all formats or EPUB only."""
    return prefs['duplicate_all_formats']

def set_duplicate_all_formats(value):
    """Set whether to duplicate all formats."""
    prefs['duplicate_all_formats'] = value
