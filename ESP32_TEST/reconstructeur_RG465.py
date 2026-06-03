import numpy as np
from PIL import Image
import os

# --- PARAMÈTRES DU FICHIER ET DE L'IMAGE ---
NOM_FICHIER_RGB = "/media/user/1C6F-CC00/img_0007.rgb"  # <--- Changez ceci par le nom de votre fichier
LARGEUR = 160                     # La largeur que vous avez définie dans le code ESP32
HAUTEUR = 120                     # La hauteur que vous avez définie dans le code ESP32
NOM_FICHIER_SORTIE = "image_ov7670.png"
TAILLE_ATTENDUE = LARGEUR * HAUTEUR * 2 # 38400 octets

def decoder_rgb565(chemin_fichier_rgb, largeur, hauteur):
    """
    Lit un fichier binaire au format RGB565 et le convertit en une image RGB standard (24 bits).
    """
    if not os.path.exists(chemin_fichier_rgb):
        print(f"Erreur : Le fichier '{chemin_fichier_rgb}' n'a pas été trouvé.")
        return None

    taille_reelle = os.path.getsize(chemin_fichier_rgb)
    if taille_reelle != TAILLE_ATTENDUE:
        print(f"Attention : Taille du fichier inattendue.")
        print(f"Taille réelle : {taille_reelle} octets. Taille attendue : {TAILLE_ATTENDUE} octets.")
        # Le script essaiera quand même de décoder, mais l'image sera probablement déformée.
        # S'il y a un problème de taille, cela indique un échec de capture/écriture sur l'ESP32.

    print(f"Lecture du fichier : {chemin_fichier_rgb}")

    # 1. Lecture des données brutes (en tant que tableau de uint16)
    # dtype='<u2' signifie "unsigned 16-bit integer, little-endian"
    # L'OV7670 envoie les octets dans un ordre qui correspond souvent à little-endian 
    # lors de l'assemblage (byte_lsb << 8) | byte_msb
    try:
        rgb565_data = np.fromfile(chemin_fichier_rgb, dtype=np.uint16)
    except Exception as e:
        print(f"Erreur lors de la lecture des données brutes : {e}")
        return None

    # Assurer que le tableau a la bonne dimension (W x H)
    if rgb565_data.size != largeur * hauteur:
        print("Erreur : Le nombre de pixels lus ne correspond pas à la résolution (W x H).")
        return None

    # 2. Séparation des canaux R, G et B à partir des 16 bits
    # Format RGB565 : RRRRRGGG GGGBBBBB
    
    # Masques :
    # R : Bits 11 à 15 (5 bits)
    # G : Bits 5 à 10 (6 bits)
    # B : Bits 0 à 4 (5 bits)

    # Canal R : 
    R = (rgb565_data >> 11) & 0b11111
    # Canal G :
    G = (rgb565_data >> 5) & 0b111111
    # Canal B :
    B = rgb565_data & 0b11111

    # 3. Mappage des canaux à 8 bits (0-255)
    # 5 bits -> 8 bits : R * (255 / 31) ≈ R * 8.22
    R = (R * 255 / 31).astype(np.uint8)
    # 6 bits -> 8 bits : G * (255 / 63) ≈ G * 4.04
    G = (G * 255 / 63).astype(np.uint8)
    # 5 bits -> 8 bits : B * (255 / 31) ≈ B * 8.22
    B = (B * 255 / 31).astype(np.uint8)

    # 4. Création du tableau RGB 24 bits (H x W x 3)
    # On empile les canaux R, G, B et on le redimensionne.
    rgb_24bit = np.stack((R, G, B), axis=-1).reshape((hauteur, largeur, 3))

    # 5. Création de l'objet Image PIL
    img = Image.fromarray(rgb_24bit, 'RGB')
    
    return img

# --- EXECUTION ---
if __name__ == "__main__":
    
    # 1. Décodage de l'image
    image_finale = decoder_rgb565(NOM_FICHIER_RGB, LARGEUR, HAUTEUR)

    if image_finale:
        # 2. Sauvegarde de l'image au format PNG (ou BMP, JPEG, etc.)
        image_finale.save(NOM_FICHIER_SORTIE)
        print(f"\nSuccès : L'image a été sauvegardée sous '{NOM_FICHIER_SORTIE}'.")
        print("Vous pouvez maintenant ouvrir ce fichier avec n'importe quel visualiseur d'images standard.")
        
        # 3. Affichage (optionnel)
        # image_finale.show()