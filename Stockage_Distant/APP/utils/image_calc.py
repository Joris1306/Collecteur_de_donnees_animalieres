import os

from matplotlib import image

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    liste_all_images = os.listdir(os.path.join(APP_ROOT, 'static', 'images'))
    print(f"Nombre total d'images : {len(liste_all_images)}")

    # for image in liste_all_images:
    liste_bytes_size = [os.stat(os.path.join(APP_ROOT, 'static', 'images', image)).st_size for image in liste_all_images]

    print(f"Taille totale des images : {sum(liste_bytes_size)} bytes")

    mean_size = sum(liste_bytes_size) / len(liste_bytes_size)
    print(f"Taille moyenne des images : {mean_size} bytes")
    print(f"Taille moyenne des images : {mean_size / 1024:.2f} KB")
    print(f"Taille moyenne des images : {mean_size / (1024 * 1024):.2f} MB")



if __name__ == "__main__":
    main()