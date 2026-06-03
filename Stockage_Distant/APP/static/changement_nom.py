import os

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(BASE_PATH, "images")

def main():
    liste_image = os.listdir(IMAGE_PATH)

    # print(liste_image)

    liste_char = list(set([c for img in liste_image for c in img]))
    liste_char.sort()

    print(liste_char)

    # for index, nom_image in enumerate(liste_image):
    #     nouveau_nom = nom_image.replace('\uf022',':')

    #     os.rename(
    #         os.path.join(IMAGE_PATH, nom_image),
    #         os.path.join(IMAGE_PATH, nouveau_nom)
    #     )

if __name__ == "__main__":
    main()