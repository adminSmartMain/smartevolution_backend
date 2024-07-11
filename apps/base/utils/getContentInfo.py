

def get_content_info(data_uri: str = ""):
    try:
        for_semicolon = data_uri.split(";")
        for_forward_slash = for_semicolon[0].split("/")
        for_two_points = for_forward_slash[0].split(":")
        for_comma = for_semicolon[1].split(",")
        
        result = {
            "content_type": for_two_points[1],
            "file_format": for_forward_slash[1],
            "content": for_comma[1]
        }
        return result
    except Exception as e:
        raise Exception("Error al procesar el contenido del archivo") from e