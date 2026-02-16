from calibre.customize import InterfaceActionBase

class EPUBTemplateMaster(InterfaceActionBase):
    name                = 'EPUB Template Master'
    description         = 'Manage EPUB templates: Create new books from templates, batch apply templates, and backup originals.'
    supported_platforms = ['windows', 'osx', 'linux']
    author              = 'Gemini User'
    version             = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    actual_plugin       = 'calibre_plugins.epub_template_master.action:EPUBTemplateMasterAction'

    def is_customizable(self):
        return True

    def config_widget(self):
        from calibre_plugins.epub_template_master.dialogs import ConfigWidget
        return ConfigWidget()

    def save_settings(self, config_widget):
        config_widget.save_settings()
