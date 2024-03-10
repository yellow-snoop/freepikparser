
from freepikparser import FreepikParser
import IPython

prompt = 'people'

try:
    parser.browser_driver.close()
except:
    pass

parser = FreepikParser()

parser.open_chrome()
parser.open_freepik_page(prompt)

parser.sc
parser.find_page_num()

parser.last_image_url = ''
# parser.n_downloaded = 0
start_page_number = parser.current_page
for n in range(start_page_number, parser.total_pages + 1):
    parser.find_images_on_page()
    parser.total_images = len(parser.images)
    parser.go_to_image(0)

    for k in range(1, parser.total_images + 1):
        print(f'Prompt = "{prompt}" | Страница {parser.current_page}/{parser.total_pages} | Картинка {k}/{parser.total_images} | Всего скачано картинок: {parser.n_downloaded}')
        parser.find_image_preview_url()
        parser.download_image_by_url(f'pictures/{prompt}_image{parser.n_downloaded + 1}.png')
        parser.n_downloaded += 1
        parser.go_to_next_image()
        IPython.display.clear_output(wait=True)
    
    parser.browser_driver.back()
    parser.go_to_next_page()
    parser.current_page += 1
