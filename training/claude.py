import anthropic
import PyPDF2
import os
import pdfplumber
import pdf2image
import pytesseract

from typing import List, Dict

class ProcesadorDocumentos:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.conversation_history = []
    
    def extraer_texto_pdf(self, pdf_path: str, doc: str) -> str:
#        """Extrae texto de un PDF"""
        texto = ""
        path = f"{pdf_path}{doc}.txt"
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as archivo:
                texto = archivo.read()
        else:
            txt = extract_text_intelligent(f"{pdf_path}{doc}")
            with open(path, 'w', encoding='utf-8') as archivo:
                archivo.write(txt)
            texto = txt
        return texto.strip()
#
#        texto = ""
#        try:
#            with open(ruta_pdf, "rb") as file:
#                reader = PyPDF2.PdfReader(file)
#                total_paginas = len(reader.pages)
#                print(f"    Extrayendo {total_paginas} páginas...")
#                
#                for i, page in enumerate(reader.pages, 1):
#                    texto += page.extract_text() + "\n\n"
#                    if i % 10 == 0:
#                        print(f"    Progreso: {i}/{total_paginas} páginas")
#                
#                return texto.strip()
#        except Exception as e:
#            return f"[Error extrayendo {ruta_pdf}: {str(e)}]"
#    
    #def cargar_documentos(self, rutas: List[str], descripciones: List[str] = None):
    def cargar_documentos(self, pdf_path, rutas):
        """Carga múltiples PDFs extrayendo el texto"""
        #if descripciones is None:
        descripciones = [f"Documento {i+1}" for i in range(len(rutas))]
        
        print("\n" + "="*60)
        print("EXTRAYENDO TEXTO DE DOCUMENTOS")
        print("="*60)
        
        documentos_texto = []
        for ruta, desc in zip(rutas, descripciones):
            print(f"\n📄 {desc} ({ruta})")
            texto = self.extraer_texto_pdf(pdf_path, ruta)
            
            # Contar palabras aproximadas
            palabras = len(texto.split())
            print(f"    ✓ Extraídas ~{palabras} palabras")
            
            documentos_texto.append(f"=== {desc} ===\n\n{texto}")
        
        # Construir mensaje inicial
        mensaje = "He extraído el contenido de los siguientes documentos:\n\n"
        mensaje += "\n\n" + "="*60 + "\n\n"
        mensaje += "\n\n".join(documentos_texto)
        mensaje += "\n\n" + "="*60
        mensaje += "\n\nConfirma que has recibido todos los documentos y proporciona un breve resumen de cada uno."
        
        self.conversation_history = [{
            "role": "user",
            "content": mensaje
        }]
        
        print("\n" + "="*60)
        print("ENVIANDO A CLAUDE...")
        print("="*60)
        
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            messages=self.conversation_history
        )
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        return response.content[0].text
    
    def ejecutar_prompt(self, prompt: str) -> str:
        """Ejecuta un prompt manteniendo el contexto"""
        self.conversation_history.append({
            "role": "user",
            "content": prompt
        })
        
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4096,
            messages=self.conversation_history
        )
        
        self.conversation_history.append({
            "role": "assistant",
            "content": response.content
        })
        
        return response.content[0].text
    
    def ejecutar_secuencia(self, prompts: Dict[str, str]) -> Dict[str, str]:
        """Ejecuta una secuencia de prompts"""
        resultados = {}
        
        for nombre, prompt in prompts.items():
            print(f"\n{'='*60}")
            print(f"{nombre.upper().replace('_', ' ')}")
            print('='*60)
            
            resultado = self.ejecutar_prompt(prompt)
            resultados[nombre] = resultado
            
            # Mostrar preview
            preview = resultado[:200] + "..." if len(resultado) > 200 else resultado
            print(preview)
        
        return resultados
    
    def guardar_informe(self, resultados: Dict[str, str], archivo: str):
        """Guarda los resultados en un archivo"""
        with open(archivo, "w", encoding="utf-8") as f:
            f.write("INFORME CONSOLIDADO\n")
            f.write("="*80 + "\n\n")
            
            for seccion, contenido in resultados.items():
                f.write(f"\n{seccion.upper().replace('_', ' ')}\n")
                f.write("-"*80 + "\n")
                f.write(contenido)
                f.write("\n\n")
        
        print(f"\n✓ Informe guardado en: {archivo}")

# ============================================================================
# EJEMPLO DE USO COMPLETO
# ============================================================================

def procesar_pdf_y_pregunta(pdf_path, docs, pregunta, api_key):
    # Inicializar
    procesador = ProcesadorDocumentos(api_key=api_key)
    
    # Cargar documentos
    try:
        confirmacion = procesador.cargar_documentos(pdf_path, docs)
        
        print("\n" + "="*60)
        print("CONFIRMACIÓN DE CLAUDE")
        print("="*60)
        print(confirmacion)
        
        # Secuencia de análisis
        resultados = procesador.ejecutar_secuencia({
            "intro": """
            Quiero que adoptes el rol de un policía municipal del municipio al que llamaremos
JÚPITER. Este agente está en una oficina de recogida de denuncias del reino de España.
Todas las denuncias que recogerás de las personas que se emplacen a denunciar hechos
en tu oficina, van a estructurarse con el mismo patrón que la fuente renombrada como
MODELO COMPARECENCIA I.A. No obstante, no entraremos por ahora en las
eximentes. Solo te centrarás en determinar el delito tras la exposición de hechos de la
persona. Recuerda, que tienes que determinar todas las circustancias del hecho de forma
pormenorizada, preguntando a la persona los datos que estimes oportunos para hacer una
exposición de los hechos tan exacta como la fuente que te aporto renombrada como
MODELO COMPARECENCIA I.A., con el fin de inferir que delito está denunciando la
persona denunciante y poder a continuación exponer fundamentado en derecho ante el
delito que nos encontramos en la narración. Recuerda que la estructura ha de ser como en
la fuente renombrada como MODELO COMPARECENCIA I.A. Dime lo que has entendido
y a continuación empezaremos la denuncia de la persona denunciante
            """,
            "questions": """
            Perfecto en lo relativo a la fundamentación jurídica. Deja por ahora ese apartado. Quiero
que como agente de la autoridad, comiences a realizar las preguntas necesarias para
alcanzar un grado de exposición de los hechos fácticos con absoluta excelencia. Por lo
tanto, tu rol es comenzar a realizar preguntas al denunciante para que responda a todas la
cuestiones que han sido obviadas en su declaración inicial. adelante.
            """
        })
#        resultados = procesador.ejecutar_secuencia({
#            "extraccion_datos": """
#                Extrae de cada documento los siguientes datos:
#                - Ingresos totales
#                - Gastos operativos
#                - Beneficio neto
#                - Margen de beneficio (%)
#                Presenta los datos en formato tabla.
#            """,
#            
#            "analisis_comparativo": """
#                Compara los 3 trimestres y analiza:
#                - Evolución de ingresos (tendencia)
#                - Cambios en gastos
#                - Variación del margen de beneficio
#                - Tendencias significativas
#            """,
#            
#            "identificacion_problemas": """
#                Identifica:
#                - Áreas de preocupación
#                - Caídas significativas
#                - Aumentos inesperados en gastos
#                - Cualquier anomalía importante
#            """,
#            
#            "informe_ejecutivo": """
#                Genera un informe ejecutivo completo que incluya:
#                1. Resumen ejecutivo (150-200 palabras)
#                2. Hallazgos principales (5 puntos clave)
#                3. Tendencias observadas
#                4. Recomendaciones estratégicas (3-5 recomendaciones)
#                5. Próximos pasos sugeridos
#            """
#        })
#        
        for seccion, contenido in resultados.items():
            print("--- ")
            print(f'{seccion}: {contenido}')
        # Guardar informe
        #procesador.guardar_informe(resultados, "informe_final.txt")
        
        print("\n" + "="*60)
        print("✅ PROCESO COMPLETADO")
        print("="*60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Archivo no encontrado - {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")




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

#def procesar_pdf_y_pregunta(pdf_path, docs, pregunta, api_key):
#    # Extraer texto del PDF
#    #with open(pdf_path, 'rb') as file:
#    #    pdf_reader = PyPDF2.PdfReader(file)
#    #    texto = ""
#    #    for pagina in pdf_reader.pages:
#    #        texto += pagina.extract_text() + "\n"
#    texto = ""
#    for doc in docs:
#        path = f"{pdf_path}{doc}.txt"
#        if os.path.exists(path):
#            with open(path, 'r', encoding='utf-8') as archivo:
#                texto += archivo.read()
#        else:
#            txt = extract_text_intelligent(f"{pdf_path}{doc}")
#            with open(path, 'w', encoding='utf-8') as archivo:
#                archivo.write(txt)
#            texto += txt
#    
#    # Crear prompt
#    prompt = f"""Aquí está el contenido de un documento PDF:
#
#{texto[:500000]}  # Limitar tamaño
#
#Basándote en el documento anterior, responde esta pregunta: {pregunta}
#
#**Formatea tu respuesta con:**
#- Párrafos claros
#- Listas con puntos cuando sea apropiado
#- Negritas para conceptos importantes
#- Títulos si es necesario
#
#Respuesta en markdown:
#"""
#    
#    # Llamar a Claude API
#    client = anthropic.Anthropic(api_key=api_key)
#    
#    response = client.messages.create(
#        model="claude-3-haiku-20240307",  # Más económico
#        max_tokens=1000,
#        messages=[{"role": "user", "content": prompt}]
#    )
#    
#    return response.content[0].text
#
