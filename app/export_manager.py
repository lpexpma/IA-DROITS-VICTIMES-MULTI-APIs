# app/export_manager.py
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

try:
    from jinja2 import Template
    JINJA_AVAILABLE = True  
except ImportError:
    JINJA_AVAILABLE = False

class ExportManager:
    """Gestionnaire d'export compatible Cloud"""
    
    def __init__(self):
        self.pdf_config = None
        if PDFKIT_AVAILABLE:
            try:
                # Configuration pour environnement avec wkhtmltopdf
                self.pdf_config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
            except:
                self.pdf_config = None
    
    def is_pdf_available(self) -> bool:
        """Vérifie si la génération PDF est disponible"""
        return PDFKIT_AVAILABLE and JINJA_AVAILABLE and self.pdf_config is not None
    
    def generer_rapport_pdf(self, data: Dict[str, Any]) -> str:
        """Génère un rapport PDF si disponible, sinon fallback JSON"""
        if not self.is_pdf_available():
            return self.generer_export_json(data)
        
        try:
            template_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Rapport OLIVIA</title>
                <style>
                    body { font-family: Arial; margin: 40px; }
                    .header { text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 20px; }
                    .section { margin: 30px 0; }
                    .texte-item { border-left: 4px solid #10B981; padding: 15px; margin: 10px 0; background: #f8fafc; }
                    .metadata { color: #6B7280; font-size: 0.9em; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>⚡ RAPPORT OLIVIA ULTIMATE</h1>
                    <p>Généré le {{timestamp}}</p>
                </div>
                
                <div class="section">
                    <h3>🎯 Situation Analysée</h3>
                    <p><strong>{{situation}}</strong></p>
                </div>
                
                {% if textes %}
                <div class="section">
                    <h3>📚 Textes Législatifs</h3>
                    {% for texte in textes %}
                    <div class="texte-item">
                        <h4>{{texte.title}}</h4>
                        <p class="metadata">{{texte.code}} • {{texte.date}}</p>
                        <p>{{texte.content}}</p>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
            </body>
            </html>
            """
            
            template = Template(template_html)
            html_content = template.render(
                situation=data["situation"],
                timestamp=datetime.now().strftime("%d/%m/%Y à %H:%M"),
                textes=data.get("textes", [])
            )
            
            pdf_path = f"rapport_olivia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            
            options = {
                'page-size': 'A4',
                'margin-top': '0.75in',
                'margin-right': '0.75in', 
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
            }
            
            pdfkit.from_string(html_content, pdf_path, options=options, configuration=self.pdf_config)
            return pdf_path
            
        except Exception as e:
            print(f"⚠️  Échec génération PDF, fallback JSON: {e}")
            return self.generer_export_json(data)
    
    def generer_export_json(self, data: Dict[str, Any]) -> str:
        """Génère un export JSON structuré"""
        export_data = {
            "metadata": {
                "application": "OLIVIA ULTIMATE",
                "version": "3.0", 
                "date_generation": datetime.now().isoformat(),
                "sources": ["Légifrance", "Judilibre"]
            },
            "analyse": {
                "situation": data["situation"],
                "strategie": data.get("strategie"),
                "timestamp": data.get("timestamp")
            },
            "resultats": {
                "textes_legislatifs": data.get("legifrance", {}).get("results", []),
                "jurisprudence": data.get("judilibre", {}).get("results", [])
            }
        }
        
        json_path = f"export_olivia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return json_path
    
    def generer_export_markdown(self, data: Dict[str, Any]) -> str:
        """Génère un export Markdown"""
        markdown_content = f"""# 📋 Rapport OLIVIA

**Situation:** {data['situation']}  
**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

## 📚 Textes Législatifs
"""
        
        for texte in data.get("legifrance", {}).get("results", []):
            markdown_content += f"""
### {texte.get('title', 'Titre non disponible')}

*{texte.get('code', 'N/A')} • {texte.get('date', 'N/A')}*

{texte.get('content', 'Contenu non disponible')}

---
"""
        
        markdown_content += "\n## ⚖️ Jurisprudence\n"
        
        for juri in data.get("judilibre", {}).get("results", []):
            markdown_content += f"""
### {juri.get('jurisdiction', 'Juridiction non précisée')}

*Décision du {juri.get('decision_date', 'N/A')}*

**Solution:** {juri.get('solution', 'Non précisée')}

{juri.get('summary', 'Non disponible')}

"""
        
        md_path = f"rapport_olivia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return md_path

# Instance globale
export_manager = ExportManager()
