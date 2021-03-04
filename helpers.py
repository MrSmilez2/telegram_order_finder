from gspread_formatting import get_user_entered_format


def get_cell_templates(sheet, formats):
    templates = {}
    for format in formats:
        templates[format] = get_user_entered_format(
            sheet, format.value
        ).backgroundColor
    return templates