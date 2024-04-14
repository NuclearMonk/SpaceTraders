from textual.widgets import DataTable


class CustomDataTable(DataTable):

    def __init__(self, title, **kwargs) -> None:
        super().__init__(**kwargs)
        self.border_title = title
        self.show_cursor = False

    def watch_has_focus(self, value: bool) -> None:
        self.show_cursor = value
        return super().watch_has_focus(value)
