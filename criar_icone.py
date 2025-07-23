from PIL import Image, ImageDraw, ImageFont
import os

def criar_icone_pdv():
    """Criar ícone para o sistema PDV"""
    try:
        # Criar imagem 256x256
        img = Image.new('RGBA', (256, 256), (45, 62, 80, 255))
        draw = ImageDraw.Draw(img)
        
        # Fundo gradiente
        for y in range(256):
            alpha = int(255 * (1 - y/256))
            color = (52, 152, 219, alpha)
            draw.line([(0, y), (256, y)], fill=color)
        
        # Desenhar caixa registradora simplificada
        # Base
        draw.rectangle([40, 160, 216, 220], fill=(236, 240, 241), outline=(52, 73, 94), width=3)
        
        # Tela
        draw.rectangle([60, 80, 196, 140], fill=(46, 204, 113), outline=(39, 174, 96), width=2)
        
        # Texto PDV
        try:
            # Tentar usar fonte sistema
            font = ImageFont.truetype("arial.ttf", 32)
        except:
            font = ImageFont.load_default()
        
        # Texto na tela
        draw.text((128, 110), "PDV", fill=(255, 255, 255), font=font, anchor="mm")
        
        # Botões caixa
        for i in range(3):
            for j in range(4):
                x = 55 + j*35
                y = 175 + i*12
                draw.rectangle([x, y, x+25, y+8], fill=(189, 195, 199), outline=(127, 140, 141))
        
        # Salvar como ICO
        img.save('icone.ico', format='ICO', sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])
        print("✅ Ícone criado: icone.ico")
        
    except Exception as e:
        print(f"❌ Erro criar ícone: {e}")
        print("💡 Continuando sem ícone personalizado...")

if __name__ == "__main__":
    # Instalar Pillow se não tiver
    try:
        from PIL import Image
    except ImportError:
        import subprocess
        subprocess.run(["pip", "install", "pillow"])
        from PIL import Image
    
    criar_icone_pdv()