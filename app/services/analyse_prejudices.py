# app/services/analyse_prejudices.py
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime

class AnalyseurPrejudicesComplexes:
    def __init__(self):
        self.categories_prejudices = {
            "psychique": {
                "mots_cles": ["séquelles psy", "traumatisme", "dépression", "anxiété", "PTSD", "stress", "psychique", "mental"],
                "description": "Troubles psychologiques et émotionnels"
            },
            "physique": {
                "mots_cles": ["blessures", "fractures", "handicap", "incapacité", "douleurs", "physique", "corporel"],
                "description": "Lésions et séquelles physiques"
            },
            "personnel": {
                "mots_cles": ["vie familiale", "intimité", "agrément", "loisirs", "familial", "personnel", "privé"],
                "description": "Impact sur la vie personnelle et familiale"
            },
            "professionnel": {
                "mots_cles": ["carrière", "évolution", "promotion", "projet", "professionnel", "travail", "emploi"],
                "description": "Conséquences sur la vie professionnelle"
            },
            "patrimonial": {
                "mots_cles": ["entreprise", "CA", "chiffre affaires", "pertes financières", "économique", "patrimonial", "commercial"],
                "description": "Préjudices économiques et financiers"
            },
            "esthétique": {
                "mots_cles": ["cicatrices", "défiguration", "apparence", "esthétique", "beauté"],
                "description": "Préjudice esthétique"
            }
        }
        
        self.requetes_specialisees = {
            "psychique": {
                "query": "trouble anxieux post-traumatique dépression séquelles psychiques expertise psychiatrique",
                "filters": {"size": 5, "sort": [{"date": "desc"}]}
            },
            "physique": {
                "query": "incapacité permanente partielle blessures séquelles physiques expertise médicale",
                "filters": {"size": 5, "sort": [{"date": "desc"}]}
            },
            "personnel": {
                "query": "préjudice d'agrément vie familiale intimité perte plaisir loisirs",
                "filters": {"size": 5, "sort": [{"date": "desc"}]}
            },
            "professionnel": {
                "query": "perte chance professionnelle évolution carrière projet entreprise développement",
                "filters": {"size": 5, "sort": [{"date": "desc"}]}
            },
            "patrimonial": {
                "query": "chef entreprise perte chiffre affaires préjudice économique dirigeant indisponibilité",
                "filters": {"size": 5, "sort": [{"date": "desc"}]}
            },
            "esthétique": {
                "query": "préjudice esthétique cicatrices défiguration apparence physique",
                "filters": {"size": 5, "sort": [{"date": "desc"}]}
            }
        }
        
        self.interactions_prejudices = {
            ("psychique", "professionnel"): "Majoration possible pour impact carrière dû aux troubles psychiques",
            ("personnel", "professionnel"): "Préjudices distincts mais souvent liés dans l'expertise",
            ("patrimonial", "professionnel"): "Attention au double comptage entre perte CA et perte chance pro",
            ("physique", "psychique"): "Séquelles physiques souvent accompagnées de conséquences psychiques"
        }

    def analyser_description(self, description: str) -> Dict[str, Any]:
        """Analyse une description et détecte les préjudices"""
        description_lower = description.lower()
        prejudices_detectes = []
        
        for categorie, config in self.categories_prejudices.items():
            if any(mot in description_lower for mot in config["mots_cles"]):
                prejudices_detectes.append({
                    "categorie": categorie,
                    "description": config["description"],
                    "confiance": self.calculer_confiance(description_lower, config["mots_cles"])
                })
        
        # Tri par confiance
        prejudices_detectes.sort(key=lambda x: x["confiance"], reverse=True)
        
        return {
            "prejudices_detectes": prejudices_detectes,
            "interactions": self.detecter_interactions([p["categorie"] for p in prejudices_detectes]),
            "complexite": "élevée" if len(prejudices_detectes) > 2 else "moyenne"
        }

    def calculer_confiance(self, description: str, mots_cles: List[str]) -> float:
        """Calcule un score de confiance pour la détection"""
        matches = sum(1 for mot in mots_cles if mot in description)
        return min(matches / len(mots_cles) * 100, 100.0)

    def detecter_interactions(self, prejudices: List[str]) -> List[str]:
        """Détecte les interactions entre préjudices"""
        interactions = []
        prejudices_set = set(prejudices)
        
        for combo, description in self.interactions_prejudices.items():
            if all(p in prejudices_set for p in combo):
                interactions.append(description)
        
        return interactions

    def construire_requetes_jurisprudence(self, prejudices: List[str]) -> Dict[str, Dict]:
        """Construit les requêtes spécialisées pour chaque préjudice"""
        requetes = {}
        for prejudice in prejudices:
            if prejudice in self.requetes_specialisees:
                requetes[prejudice] = self.requetes_specialisees[prejudice]
        
        return requetes

    def estimer_indemnisation(self, prejudices: List[str]) -> Dict[str, Any]:
        """Fournit une estimation indicative des indemnisations (barème interne non officiel)"""
        baremes_indicatifs = {
            "psychique": {"min": 10000, "max": 50000, "unite": "€", "source": "barème interne indicatif"},
            "physique": {"min": 15000, "max": 80000, "unite": "€", "source": "barème interne indicatif"},
            "personnel": {"min": 8000, "max": 40000, "unite": "€", "source": "barème interne indicatif"},
            "professionnel": {"min": 10000, "max": 60000, "unite": "€", "source": "barème interne indicatif"},
            "patrimonial": {"min": 20000, "max": 100000, "unite": "€", "source": "barème interne indicatif"},
            "esthétique": {"min": 5000, "max": 30000, "unite": "€", "source": "barème interne indicatif"}
        }
        
        estimations = {}
        total_min = 0
        total_max = 0
        
        for prejudice in prejudices:
            if prejudice in baremes_indicatifs:
                estimations[prejudice] = baremes_indicatifs[prejudice]
                total_min += baremes_indicatifs[prejudice]["min"]
                total_max += baremes_indicatifs[prejudice]["max"]
        
        return {
            "estimations_par_prejudice": estimations,
            "total_estime": {"min": total_min, "max": total_max, "unite": "€", "source": "barème interne indicatif"},
            "recommendations_calcul": [
                "Les montants sont indicatifs et basés sur un barème interne non officiel",
                "Une expertise médicale et économique est nécessaire pour préciser les montants",
                "Les préjudices complexes nécessitent souvent une majoration",
                "Ces estimations ne remplacent pas une expertise judiciaire"
            ]
        }