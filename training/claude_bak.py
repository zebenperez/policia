import anthropic
import PyPDF2
import os
import pdfplumber
import pdf2image
import pytesseract


def extract_text_from_scanned_pdf(pdf_path):
    """
    Extrae texto de PDFs escaneados o con imágenes usando OCR
    """
    try:
        # Convertir PDF a imágenes
        print("Convirtiendo PDF a imágenes...")
        images = pdf2image.convert_from_path(pdf_path)

        full_text = ""

        for i, image in enumerate(images):
            print(f"Procesando página {i+1}/{len(images)}...")

            # Aplicar OCR a cada imagen
            text = pytesseract.image_to_string(image, lang='spa')  # 'spa' para español
            full_text += f"\n--- Página {i+1} ---\n{text}\n"

        return full_text

    except Exception as e:
        print(f"Error en OCR: {e}")
        return None

def extract_text_with_pdfplumber(pdf_path):
    """
    pdfplumber es mejor que PyPDF2 para extraer texto
    """
    try:
        full_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                print(f"Extrayendo texto página {i+1}...")
                text = page.extract_text()
                if text:
                    full_text += f"\n--- Página {i+1} ---\n{text}\n"
                else:
                    print(f"Página {i+1}: No se pudo extraer texto (posible imagen)")

        return full_text if full_text.strip() else None

    except Exception as e:
        print(f"Error con pdfplumber: {e}")
        return None

def extract_text_intelligent(pdf_path, use_ocr=True):
    """
    Intenta primero con pdfplumber, si falla usa OCR
    """
    print("Intentando extracción con pdfplumber...")
    text_pdfplumber = extract_text_with_pdfplumber(pdf_path)

    if text_pdfplumber and len(text_pdfplumber.strip()) > 100:  # Si hay suficiente texto
        print("✅ Texto extraído con pdfplumber")
        return text_pdfplumber
    elif use_ocr:
        print("❌ Poco texto extraído, usando OCR...")
        text_ocr = extract_text_from_scanned_pdf(pdf_path)
        return text_ocr
    else:
        return text_pdfplumber

def procesar_pdf_y_pregunta(pdf_path, docs, pregunta, api_key):
    # Extraer texto del PDF
    #with open(pdf_path, 'rb') as file:
    #    pdf_reader = PyPDF2.PdfReader(file)
    #    texto = ""
    #    for pagina in pdf_reader.pages:
    #        texto += pagina.extract_text() + "\n"
    texto = ""
    for doc in docs:
        path = f"{pdf_path}{doc}.txt"
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as archivo:
                texto += archivo.read()
        else:
            txt = extract_text_intelligent(f"{pdf_path}{doc}")
            with open(path, 'w', encoding='utf-8') as archivo:
                archivo.write(txt)
            texto += txt
    
    # Crear prompt
    prompt = f"""Aquí está el contenido de un documento PDF:

{texto[:500000]}  # Limitar tamaño

Basándote en el documento anterior, responde esta pregunta: {pregunta}

**Formatea tu respuesta con:**
- Párrafos claros
- Listas con puntos cuando sea apropiado
- Negritas para conceptos importantes
- Títulos si es necesario

Respuesta en markdown:
"""
    
    # Llamar a Claude API
    client = anthropic.Anthropic(api_key=api_key)
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",  # Más económico
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

def chat_interactivo_pdf(pdf_path, api_key):
    # Extraer texto una sola vez
    print("Extrayendo texto del PDF...")
    texto = extract_text_intelligent(pdf_path)

    if not texto:
        print("❌ No se pudo extraer texto del PDF")
        return

    print(f"✅ Texto extraído ({len(texto)} caracteres)")

    # Limitar tamaño si es muy grande
    if len(texto) > 100000:
        texto = texto[:100000]
        print("⚠️  Texto recortado a 100,000 caracteres")

    # Crear contexto base
    contexto_base = f"""Aquí está el contenido de un documento PDF:

{texto}

Basándote en este documento, responde mis preguntas:"""

    # Inicializar cliente y historial
    client = anthropic.Anthropic(api_key=api_key)
    historial = [{"role": "user", "content": contexto_base}]
    print("\n" + "="*50)
    print("💬 CHAT INTERACTIVO CON EL PDF")
    print("Escribe 'salir' para terminar")
    print("Escribe 'nuevo' para reiniciar la conversación")
    print("="*50)
    
    while True:
        pregunta = input("\n🧠 Tu pregunta: ").strip()
        
        if pregunta.lower() in ['salir', 'exit', 'quit']:
            print("👋 ¡Hasta luego!")
            break
        elif pregunta.lower() in ['nuevo', 'reset', 'reiniciar']:
            historial = [{"role": "user", "content": contexto_base}]
            print("🔄 Conversación reiniciada")
            continue
        elif not pregunta:
            continue
        try:
            # Agregar pregunta al historial
            historial.append({"role": "user", "content": pregunta})
            
            # Llamar a Claude
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=historial
            )
            
            respuesta = response.content[0].text
            
            # Agregar respuesta al historial
            historial.append({"role": "assistant", "content": respuesta})
            
            print(f"\n🤖 Claude: {respuesta}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

# Ejemplo de uso
#pdf_path = "./memoria.pdf"
#pdf_path = "./comparecencia.pdf"
#pregunta = "¿Cuál es el tema principal de este documento?"
#pregunta = "¿Cuál es el CIF de la empresa?"

#chat_interactivo_pdf(pdf_path, api_key)
#respuesta = procesar_pdf_y_pregunta(pdf_path, pregunta, api_key)
#print(respuesta)
