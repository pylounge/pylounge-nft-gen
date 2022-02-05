from collections import Counter
from random import choices, randint
import struct
import os
from typing import List, Tuple
from PIL import Image


def get_files_from_folder(path:str, with_none:bool=False) -> str:
    '''
    Retrieves all files from a folder
    
    :param path:  //TODO
    :param with_none: //TODO 
    :returns: //TODO
    '''
    pictures: List[str] = []
    with os.scandir(path) as listOfEntries:  
        for entry in listOfEntries:
            if entry.is_file():
                if entry.name.endswith('.png'):
                    pictures.append(entry.path)
    if with_none:
        pictures.append('None')
    return pictures

def generate_img(result_img:str, elements:List[Tuple[str, List[int], bool]],
                 elements_for_repainting:List[str], pic_num:str='') -> None:
    def _colorize_img(img:str, count_colors:int) -> str:
        colors = get_most_common_img_colors(img, count_colors + 1)[1:] # !!!
        if colors:
            main_color_hex = get_random_hex_color()
            main_color_rgb = get_rgb_color_from_hex(main_color_hex)

            color_step = 30 

            # rgba (225,255,200, 0.1)
            subcolor1_rgb = (main_color_rgb[0] - color_step, main_color_rgb[1], main_color_rgb[2]) 
            subcolor2_rgb = (main_color_rgb[0], main_color_rgb[1], main_color_rgb[2] + color_step)

            subcolor1_hex = get_hex_color_from_rgb(subcolor1_rgb[0], subcolor1_rgb[1], subcolor1_rgb[2])
            subcolor2_hex = get_hex_color_from_rgb(subcolor2_rgb[0], subcolor2_rgb[1], subcolor2_rgb[2])

            alternate_colors = [main_color_hex, subcolor1_hex, subcolor2_hex] 
            alternate_colors = alternate_colors[:len(colors)]
            
            colors = [pair[0] for pair in colors]
            for color in zip(colors, alternate_colors):
                img = changePNGColor(img, color[0], color[1], img)
        return img
    
    # список выпавших элементов для описания
    desc_items: List[str] = []

    for element in elements:
        name, weights, with_none = element
        
        items = get_files_from_folder(name, with_none=with_none)
        item = choices(items, weights)[0]

        if item != 'None':
            if name.find('Фон') != -1:
                result_img = item
            else:
                desc_items.append(item) # записали элемент
                if elements_for_repainting: # если есть элементы для перекрашивания 
                    if name in elements_for_repainting: # если элемент относится к элементом для перекрашивания
                        COLORS = 3 # сколько цветов перекрашивать
                        item = _colorize_img(item, COLORS) # перекрашиваем
                result_img = apply_layer_to_image(result_img, item) # накладываем слой
         
    os.rename(result_img, str(pic_num) + result_img)
    make_desc_file(str(pic_num) + result_img, desc_items)
    

def make_desc_file(picture: str, items:List[str]) -> None:
    '''
    Records the layers that make up the image
    
    :param picture:  //TODO
    :param items:  //TODO
    :returns: //TODO
    '''
    FILE_EXSTENSION = '.txt'
    # 1.png 1 + '.txt'
    picture_file_txt: str = picture.split('.')[0] + FILE_EXSTENSION
    with open(picture_file_txt, 'w') as file:
        for item in items:
            item_without_num: str = item.split('-')[1]
            item_without_num_and_extension: str = item_without_num.split('.')[0]
            file.write(item_without_num_and_extension + "\n")

def get_random_hex_color() -> None:
    '''
    Generates a random color in hexadecimal format
    '''
    hex_color: str = '#{:02x}{:02x}{:02x}'.format(*map(lambda _: randint(0, 256), range(3)))
    return hex_color

def get_hex_color_from_rgb(r:int, g:int, b:int) -> str:
    '''
    Converts RGB color to hexadecimal format

    :param r:  Intensity of the color RED as an integer between 0 and 255
    :param g:  Intensity of the color GREEN as an integer between 0 and 255
    :param b:  Intensity of the color BLUE as an integer between 0 and 255
    :returns: A string containing a color in HEX format
    :exception ValueError: If the argument is not int or float
    '''
    def _chkarg(a) -> int:
        '''
        Sets the color value in the range 0-255
        '''
        if isinstance(a, int): # clamp to range 0--255
            if a < 0:
                a = 0
            elif a > 255:
                a = 255
        elif isinstance(a, float): # clamp to range 0.0--1.0 and convert to integer 0--255
            if a < 0.0:
                a = 0
            elif a > 1.0:
                a = 255
            else:
                a = int(round(a*255))
        else:
            raise ValueError('Arguments must be integers or floats.')
        return a
    r = _chkarg(r)
    g = _chkarg(g)
    b = _chkarg(b)
    return '#{:02x}{:02x}{:02x}'.format(r,g,b)


def changePNGColor(source_file:str, from_rgb:str, to_rgb:str, path_to_save:str = '', delta_rank:int = 10) -> str:
    '''
    Changes the color of the image elements
    
    :param original_img_path:  //TODO
    :param layer_img_path: //TODO 
    :param path_to_save:  //TODO
    :exception Exception: //TODO
    :returns: A path for new img
    '''
    from_rgb: str = from_rgb.replace('#', '')
    to_rgb: str = to_rgb.replace('#', '')

    try:
        from_color: Tuple[int, int] = struct.unpack('BBB', bytes.fromhex(from_rgb))
        to_color: Tuple[int, int] = struct.unpack('BBB', bytes.fromhex(to_rgb))
    except Exception:
        return path_to_save

    img: Image.Image = Image.open(source_file)
    img: Image.Image = img.convert("RGBA")
    pixdata = img.load()

    for x in range(0, img.size[0]):
        for y in range(0, img.size[1]):
            rdelta = pixdata[x, y][0] - from_color[0]
            gdelta = pixdata[x, y][0] - from_color[0]
            bdelta = pixdata[x, y][0] - from_color[0]
            if abs(rdelta) <= delta_rank and abs(gdelta) <= delta_rank and abs(bdelta) <= delta_rank:
                pixdata[x, y] = (to_color[0] + rdelta, to_color[1] + gdelta, to_color[2] + bdelta, pixdata[x, y][3])

    if path_to_save:
        path_to_save = path_to_save[:path_to_save.rfind('.')] + '_' + path_to_save[path_to_save.rfind('.'):]
    else:
        path_to_save = source_file[:source_file.rfind('.')] + '_' + source_file[source_file.rfind('.'):] 
    img.save(path_to_save)
    return path_to_save

def get_most_common_img_colors(image_path:str, num_colors:int) -> List[Tuple[str, int]]:
    '''
    Returns the most dominant colors in the occupied area of the image
    
    :param original_img_path:  //TODO
    :param layer_img_path: //TODO 
    :param path_to_save:  //TODO
    :exception Exception: //TODO
    :returns: //TODO
    '''
    def _get_every_pixel_color(image_path):
        im: Image.Image = Image.open(image_path, 'r')
        pixel_values = list(im.getdata())
        return pixel_values
    
    set_colors: List[str] = []
    for color in _get_every_pixel_color(image_path):
        set_colors.append(get_hex_color_from_rgb(color[0], color[1], color[2]))
    return Counter(set_colors).most_common(num_colors)

def apply_layer_to_image(original_img_path:str, layer_img_path:str, path_to_save:str='') -> str:
    '''
    Overlays one image on another
    
    :param original_img_path:  //TODO
    :param layer_img_path: //TODO 
    :param path_to_save:  //TODO
    :returns: A path for new img
    '''
    
    IMG_POSTFIX =  '_res.png'
    
    original_img: Image.Image = Image.open(original_img_path).convert("RGBA")
    layer_img: Image.Image = Image.open(layer_img_path).convert("RGBA")
    
    x, y = layer_img.size
    
    original_img.paste(layer_img, (0, 0, x, y),  layer_img)
    
    path_to_save = path_to_save if path_to_save else IMG_POSTFIX
    original_img.save(path_to_save)
    
    return path_to_save


def get_rgb_color_from_hex(hex_color:str) -> Tuple[int, int]:
    '''
    Converts hex representation of color to rgb
    
    :param hex_color:  //TODO
    :returns: //TODO
    '''
    hex_color:str = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def clear_tmp_files(path:str) -> None:
    '''
    Clear tmp files
    '''
    with os.scandir(path) as listOfEntries:  
        for entry in listOfEntries:
            if entry.is_file():
                if entry.name.find('_') != -1:
                    os.remove(entry.path)
    
# устанавливаем рабочую директорию
os.chdir(os.path.dirname(__file__))

def main(count_of_images):
    # ФОН > КРЫЛЬЯ > ТЕЛО > ОДЕЖДА > ПРИЧЁСКИ > МЕЧИ > АКСЕССУАРЫ
    
    probability_wieghts_background = [1, 1, 1, 1, 1, 1, 1] # вероятности фона
    probability_wieghts_wings = [2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 10] # веротяности крыльев
    probability_wieghts_body = [1, 1, 8, 8, 8] # вероятности тела
    probability_wieghts_cloth = [3, 3, 5, 5, 4, 4, 1, 1, 4, 1] # вероятности одежды 
    probability_wieghts_hairs = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1] # вероятности причёски
    probability_wieghts_sword = [5, 5, 5, 5, 5, 2, 2, 2, 2, 2, 10] # вероятности оружия
    probability_wieghts_acc = [1, 1, 1, 1, 10] # вероятности аксессуаров

    #( Название папки с элементом рисунка, список вероятностей для каждого элемента, может ли не выпасть элемент )
    elements = [('Фон/', probability_wieghts_background, False), ('Тело/', probability_wieghts_body, False),
               ('Крылья/', probability_wieghts_wings, True), ('Одежда/', probability_wieghts_cloth, False),
               ('Прически/', probability_wieghts_hairs, False), ('Оружее/', probability_wieghts_sword, True),
               ('Аксессуары/',probability_wieghts_acc, True)]
    # список элементов, которые надо перекрашивать
    elements_for_repainting = ['Крылья/', 'Одежда/', 'Прически/', 'Оружее/']
    # итоговое изображение 
    result_img = ''

    for i in range(1, count_of_images + 1):
        generate_img(result_img, elements, elements_for_repainting, i)
        # чистим временные файлы, которые создаются при перекрашивании 
        for element in elements_for_repainting:
            clear_tmp_files(element)

if __name__ == '__main__':
    try:
        COUNT_OF_IMAGES = 5
        main(COUNT_OF_IMAGES)
    except KeyboardInterrupt:
        exit()


