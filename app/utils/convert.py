import base64


def decode_image(b64_avatar):
    '''
    Переводит картинку base64 в байтовый формат
    :param b64_avatar:
    :return:
    '''
    return base64.b64decode(b64_avatar.split(',')[1])


def encode_image(byte_avatar):
    '''
    Переводит байты картинки в формат base64
    :param byte_avatar:
    :return:
    '''
    avatar = base64.b64encode(byte_avatar).decode("utf-8") if byte_avatar else ''
    return f"data:image/png;base64,{avatar}" if avatar else ''
