# app/analyse_victime.py
# =========================
# SYSTÈME EXPERT D'ANALYSE POUR LA DÉFENSE DES VICTIMES
# =========================

import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date

class AnalyseurVictime:
    """Système expert d'analyse pour la défense et l'indemnisation des victimes"""
    
    def __init__(self):
        self.baremes_reference = self._charger_baremes()
        self.mots_cles_specifiques = self._charger_mots_cles()
    
    def _charger_baremes(self) -> Dict[str, Any]:
        """Charge les barèmes de référence pour l'indemnisation"""
        return {
            "dfp_taux_ipp": {
                "tres_leger": (1, 5, 1000, 2000),
                "leger": (6, 15, 2000, 3000),
                "moyen": (16, 30, 3000, 4500),
                "important": (31, 50, 4500, 7000),
                "grave": (51, 70, 7000, 12000),
                "tres_grave": (71, 100, 12000, 25000)
            },
            "souffrances_endurees": {
                "tres_faible": (1, 2, 500, 1500),
                "faible": (3, 4, 1500, 3000),
                "moyen": (5, 6, 3000, 6000),
                "important": (7, 8, 6000, 10000),
                "tres_important": (9, 10, 10000, 20000)
            }
        }
    
    def _charger_mots_cles(self) -> Dict[str, List[str]]:
        """Charge les mots-clés pour l'analyse sémantique"""
        return {
            "gravite_lesions": [
                "fracture", "traumatisme", "commotion", "luxation", "entorse grave",
                "lesion musculaire", "dechirure", "rupture", "hematome important",
                "plaie profonde", "brulure", "cicatrice", "sequelle"
            ],
            "soins_intensifs": [
                "chirurgie", "operation", "intervention", "hospitalisation",
                "reanimation", "soins intensifs", "kinesitherapie", "reeducation",
                "prothese", "orthèse", "fauteuil roulant", "ambulance"
            ],
            "impact_vie_quotidienne": [
                "aide menagere", "tierce personne", "accompagnement", "dependance",
                "autonomie reduite", "difficulte deplacement", "handicap",
                "incapacite", "invalidite", "amenagement logement", "vehicule adapte"
            ],
            "impact_professionnel": [
                "arret travail", "incapacite temporaire", "incapacite permanente",
                "reclassement", "reconversion", "licenciement", "perte emploi",
                "diminution salaire", "incidence professionnelle", "inaptitude"
            ],
            "souffrances_psychologiques": [
                "depression", "anxiete", "stress post traumatique", "insomnie",
                "phobie", "cauchemars", "irritabilite", "crise angoisse",
                "suivi psychologique", "psychiatre", "therapie", "traumatisme psychique"
            ]
        }
    
    def analyser_situation_complete(self, description: str, role: str = "victime") -> Dict[str, Any]:
        """Analyse complète de la situation pour la défense de la victime"""
        
        texte_nettoye = self._nettoyer_texte(description)
        
        return {
            "metadata": {
                "date_analyse": datetime.now().isoformat(),
                "longueur_texte": len(texte_nettoye),
                "mots_cles_trouves": self._compter_mots_cles(texte_nettoye),
                "mode": "expert"
            },
            "analyse_prejudices": self._analyser_prejudices_detailles(texte_nettoye, role),
            "elements_defense": self._identifier_elements_defense(texte_nettoye, role),
            "strategie_indemnisation": self._elaborer_strategie_indemnisation(texte_nettoye),
            "textes_applicables": self._identifier_textes_applicables(texte_nettoye, role),
            "risques_obstacles": self._identifier_risques_obstacles(texte_nettoye),
            "preuves_necessaires": self._lister_preuves_necessaires(texte_nettoye),
            "recommandations_actions": self._generer_recommandations(texte_nettoye, role)
        }
    
    def _nettoyer_texte(self, texte: str) -> str:
        """Nettoie et prépare le texte pour l'analyse"""
        if not texte:
            return ""
        texte_propre = re.sub(r'[^\w\s.,;!?()\-]', ' ', texte.lower())
        texte_propre = re.sub(r'\s+', ' ', texte_propre).strip()
        return texte_propre
    
    def _compter_mots_cles(self, texte: str) -> Dict[str, int]:
        """Compte les occurrences des mots-clés par catégorie"""
        resultats = {}
        for categorie, mots in self.mots_cles_specifiques.items():
            compteur = 0
            for mot in mots:
                compteur += len(re.findall(r'\b' + re.escape(mot) + r'\b', texte))
            resultats[categorie] = compteur
        return resultats
    
    def _analyser_prejudices_detailles(self, texte: str, role: str) -> Dict[str, Any]:
        """Analyse détaillée de tous les préjudices identifiables"""
        
        return {
            "prejudices_patrimoniaux": self._analyser_prejudices_patrimoniaux(texte, role),
            "prejudices_extrapatrimoniaux": self._analyser_prejudices_extrapatrimoniaux(texte, role),
            "prejudices_affectifs": self._analyser_prejudices_affectifs(texte, role),
            "score_gravite_globale": self._calculer_score_gravite(texte)
        }
    
    def _analyser_prejudices_patrimoniaux(self, texte: str, role: str) -> Dict[str, Any]:
        """Analyse des préjudices patrimoniaux"""
        
        prejudices = {}
        
        # Frais médicaux
        if any(mot in texte for mot in ["hopital", "clinique", "medecin", "kine", "pharmacie"]):
            prejudices["frais_medicaux"] = {
                "present": True,
                "description": "Frais de santé engagés (consultations, soins, médicaments)",
                "estimation": "À quantifier sur justificatifs",
                "confiance": 0.8
            }
        
        # Pertes de gains professionnels
        if any(mot in texte for mot in ["arret travail", "salaire", "emploi", "revenu"]):
            duree_arret = self._estimer_duree_arret(texte)
            prejudices["pertes_gains"] = {
                "present": True,
                "description": "Perte de revenus professionnels pendant l'arrêt de travail",
                "duree_estimee": duree_arret,
                "estimation": f"Calcul sur {duree_arret} mois de salaire",
                "confiance": 0.7
            }
        
        # Incidence professionnelle
        if any(mot in texte for mot in ["reconversion", "inaptitude", "changement poste"]):
            prejudices["incidence_professionnelle"] = {
                "present": True,
                "description": "Impact durable sur la carrière et les perspectives professionnelles",
                "gravite": "À expertiser médicalement",
                "confiance": 0.6
            }
        
        return prejudices
    
    def _analyser_prejudices_extrapatrimoniaux(self, texte: str, role: str) -> Dict[str, Any]:
        """Analyse des préjudices extrapatrimoniaux"""
        
        prejudices = {}
        
        # Déficit fonctionnel permanent
        taux_ipp = self._estimer_taux_ipp(texte)
        if taux_ipp > 0:
            prejudices["deficit_fonctionnel_permanent"] = {
                "present": True,
                "taux_estime": taux_ipp,
                "description": f"Incidence permanente sur l'intégrité physique/fonctionnelle - IPP estimée à {taux_ipp}%",
                "estimation_euros": self._estimer_valeur_ipp(taux_ipp),
                "confiance": 0.7
            }
        
        # Souffrances endurées
        niveau_se = self._evaluer_souffrances_endurees(texte)
        if niveau_se > 0:
            prejudices["souffrances_endurees"] = {
                "present": True,
                "niveau": niveau_se,
                "description": f"Souffrances physiques et psychiques - Niveau {niveau_se}/10",
                "estimation_euros": f"{niveau_se * 1500:,} €".replace(",", " "),
                "confiance": 0.6
            }
        
        # Préjudice esthétique
        if any(mot in texte for mot in ["cicatrice", "disfiguration", "esthetique"]):
            prejudices["prejudice_esthetique"] = {
                "present": True,
                "description": "Atteinte à l'intégrité physique visible et à l'apparence",
                "estimation_euros": "2 000 - 15 000 € selon gravité",
                "confiance": 0.5
            }
        
        # Préjudice d'agrément
        if any(mot in texte for mot in ["loisir", "sport", "activite", "passetemps"]):
            prejudices["prejudice_agrement"] = {
                "present": True,
                "description": "Impossibilité de pratiquer des activités de loisir et de détente",
                "estimation_euros": "1 000 - 10 000 €",
                "confiance": 0.4
            }
        
        return prejudices
    
    def _analyser_prejudices_affectifs(self, texte: str, role: str) -> Dict[str, Any]:
        """Analyse des préjudices affectifs"""
        
        prejudices = {}
        
        if any(mot in texte for mot in ["famille", "conjoint", "enfant", "proche"]):
            prejudices["prejudice_affection"] = {
                "present": True,
                "description": "Souffrance des proches de la victime directe",
                "beneficiaires": "Conjoint, enfants, parents directs",
                "estimation_euros": "5 000 - 30 000 € par bénéficiaire",
                "confiance": 0.5
            }
        
        return prejudices
    
    def _estimer_taux_ipp(self, texte: str) -> int:
        """Estime le taux d'incapacité permanente partielle"""
        taux = 0
        
        if any(mot in texte for mot in ["fracture", "operation", "chirurgie"]):
            taux += 5
        if any(mot in texte for mot in ["sequelle", "handicap", "incapacite"]):
            taux += 10
        if any(mot in texte for mot in ["deplacement", "fauteuil", "canne"]):
            taux += 15
        if any(mot in texte for mot in ["douleur chronique", "invalidite"]):
            taux += 20
        
        return min(taux, 100)
    
    def _estimer_valeur_ipp(self, taux_ipp: int) -> str:
        """Estime la valeur financière de l'IPP"""
        for niveau, (min_taux, max_taux, min_val, max_val) in self.baremes_reference["dfp_taux_ipp"].items():
            if min_taux <= taux_ipp <= max_taux:
                valeur = (taux_ipp - min_taux) * (max_val - min_val) // (max_taux - min_taux) + min_val
                return f"{valeur:,} €".replace(",", " ")
        return "À expertiser"
    
    def _estimer_duree_arret(self, texte: str) -> int:
        """Estime la durée d'arrêt de travail en mois"""
        duree = 0
        
        if any(mot in texte for mot in ["arret travail", "arret maladie"]):
            duree += 1
        if any(mot in texte for mot in ["prolongation", "reprise progressive"]):
            duree += 2
        if any(mot in texte for mot in ["incapacite temporaire", "convalescence"]):
            duree += 3
        
        return max(duree, 1)
    
    def _evaluer_souffrances_endurees(self, texte: str) -> int:
        """Évalue le niveau de souffrances endurées sur 10"""
        niveau = 0
        
        if any(mot in texte for mot in ["douleur", "souffrance"]):
            niveau += 3
        if any(mot in texte for mot in ["traumatisme", "stress", "angoisse"]):
            niveau += 2
        if any(mot in texte for mot in ["depression", "insomnie", "cauchemar"]):
            niveau += 3
        if any(mot in texte for mot in ["hospitalisation", "reanimation"]):
            niveau += 2
        
        return min(niveau, 10)
    
    def _calculer_score_gravite(self, texte: str) -> int:
        """Calcule un score global de gravité sur 100"""
        score = 0
        
        if any(mot in texte for mot in self.mots_cles_specifiques["gravite_lesions"]):
            score += 30
        if any(mot in texte for mot in self.mots_cles_specifiques["soins_intensifs"]):
            score += 25
        if any(mot in texte for mot in self.mots_cles_specifiques["impact_vie_quotidienne"]):
            score += 20
        if any(mot in texte for mot in self.mots_cles_specifiques["impact_professionnel"]):
            score += 15
        if any(mot in texte for mot in self.mots_cles_specifiques["souffrances_psychologiques"]):
            score += 10
        
        return min(score, 100)
    
    def _identifier_elements_defense(self, texte: str, role: str) -> List[Dict[str, Any]]:
        """Identifie les éléments juridiques pour la défense de la victime"""
        
        elements = []
        
        # Régime de responsabilité
        if any(mot in texte for mot in ["accident circulation", "voiture", "conducteur"]):
            elements.append({
                "categorie": "Régime spécial",
                "element": "Application loi Badinter - indemnisation facilitée",
                "force": "Très élevée",
                "description": "La victime d'accident de la circulation bénéficie d'un régime d'indemnisation plus favorable",
                "textes_reference": ["Loi 85-677 du 5 juillet 1985"]
            })
        
        # Élément de faute
        if any(mot in texte for mot in ["imprudence", "negligence", "faute", "vitesse", "alcool"]):
            elements.append({
                "categorie": "Responsabilité",
                "element": "Faute du responsable identifiée",
                "force": "Élevée",
                "description": "La faute du responsable engage sa responsabilité civile",
                "textes_reference": ["Code civil 1240", "Code civil 1241"]
            })
        
        # Gravité des préjudices
        if self._calculer_score_gravite(texte) > 50:
            elements.append({
                "categorie": "Gravité",
                "element": "Préjudices graves et multiples",
                "force": "Élevée",
                "description": "La gravité des préjudices justifie une indemnisation importante",
                "textes_reference": ["Nomenclature Dintilhac"]
            })
        
        return elements
    
    def _elaborer_strategie_indemnisation(self, texte: str) -> Dict[str, Any]:
        """Élabore une stratégie d'indemnisation"""
        
        score_gravite = self._calculer_score_gravite(texte)
        
        return {
            "estimation_globale": {
                "fourchette_basse": self._estimer_indemnisation_min(texte),
                "fourchette_haute": self._estimer_indemnisation_max(texte),
                "fourchette_probable": self._estimer_indemnisation_probable(texte)
            },
            "points_negociation": self._identifier_points_negociation(texte),
            "argumentaire_cle": self._preparer_argumentaire_cle(texte),
            "delais_urgence": self._identifier_delais_urgence(texte)
        }
    
    def _estimer_indemnisation_min(self, texte: str) -> str:
        score = self._calculer_score_gravite(texte)
        if score < 30:
            return "5 000 - 15 000 €"
        elif score < 60:
            return "15 000 - 50 000 €"
        else:
            return "50 000 - 100 000 €"
    
    def _estimer_indemnisation_max(self, texte: str) -> str:
        score = self._calculer_score_gravite(texte)
        if score < 30:
            return "15 000 - 30 000 €"
        elif score < 60:
            return "50 000 - 150 000 €"
        else:
            return "100 000 - 300 000 €"
    
    def _estimer_indemnisation_probable(self, texte: str) -> str:
        score = self._calculer_score_gravite(texte)
        if score < 30:
            return "8 000 - 20 000 €"
        elif score < 60:
            return "25 000 - 80 000 €"
        else:
            return "70 000 - 180 000 €"
    
    def _identifier_points_negociation(self, texte: str) -> List[str]:
        points = []
        
        if any(mot in texte for mot in ["ipp", "incapacite"]):
            points.append("Taux d'IPP - négociation sur l'évaluation médicale")
        
        if any(mot in texte for mot in ["souffrance", "douleur"]):
            points.append("Niveau des souffrances endurées - argumentation sur l'intensité")
        
        if any(mot in texte for mot in ["arret travail", "salaire"]):
            points.append("Pertes de gains - calcul et projection")
        
        return points
    
    def _preparer_argumentaire_cle(self, texte: str) -> List[str]:
        argumentaire = []
        
        score_gravite = self._calculer_score_gravite(texte)
        
        if score_gravite > 60:
            argumentaire.append("Gravité exceptionnelle justifiant une indemnisation à la hauteur des préjudices subis")
        
        if any(mot in texte for mot in ["hospitalisation", "chirurgie"]):
            argumentaire.append("Parcours médical lourd démontrant l'importance des préjudices")
        
        return argumentaire
    
    def _identifier_delais_urgence(self, texte: str) -> List[str]:
        return [
            "Délai de prescription : 10 ans à compter de la consolidation",
            "Délai pour constituer le dossier médical : 3 mois"
        ]
    
    def _identifier_textes_applicables(self, texte: str, role: str) -> List[Dict[str, str]]:
        textes = []
        
        textes.append({
            "texte": "Code civil - Responsabilité civile",
            "reference": "Articles 1240 à 1242",
            "applicabilite": "Fondement général de la responsabilité"
        })
        
        if any(mot in texte for mot in ["accident circulation", "voiture"]):
            textes.append({
                "texte": "Loi Badinter",
                "reference": "Loi 85-677 du 5 juillet 1985",
                "applicabilite": "Régime spécial accidents de la circulation"
            })
        
        textes.append({
            "texte": "Nomenclature Dintilhac",
            "reference": "Référentiel d'indemnisation",
            "applicabilite": "Classification des préjudices corporels"
        })
        
        return textes
    
    def _identifier_risques_obstacles(self, texte: str) -> List[Dict[str, str]]:
        risques = []
        
        if not any(mot in texte for mot in ["medical", "hopital", "docteur"]):
            risques.append({
                "risque": "Preuves médicales insuffisantes",
                "impact": "Élevé",
                "solution": "Rassembler tous les certificats et comptes-rendus médicaux"
            })
        
        return risques
    
    def _lister_preuves_necessaires(self, texte: str) -> List[Dict[str, str]]:
        preuves = []
        
        preuves.append({
            "categorie": "Médicale",
            "preuve": "Certificats médicaux initiaux et de consolidation",
            "urgence": "Élevée"
        })
        
        preuves.append({
            "categorie": "Médicale", 
            "preuve": "Comptes-rendus d'hospitalisation et d'intervention",
            "urgence": "Élevée"
        })
        
        preuves.append({
            "categorie": "Financière",
            "preuve": "Bulletins de salaire et attestation employeur",
            "urgence": "Moyenne"
        })
        
        return preuves
    
    def _generer_recommandations(self, texte: str, role: str) -> List[Dict[str, Any]]:
        recommandations = []
        
        score_gravite = self._calculer_score_gravite(texte)
        
        if score_gravite > 40:
            recommandations.append({
                "action": "Consulter un médecin-conseil de victimes",
                "priorite": "Élevée",
                "delai": "1 mois",
                "objectif": "Évaluation médicale indépendante"
            })
        
        recommandations.append({
            "action": "Rassembler l'ensemble des preuves médicales",
            "priorite": "Élevée",
            "delai": "2 semaines",
            "objectif": "Constituer le dossier probatoire"
        })
        
        return recommandations

# Instance globale
analyseur = AnalyseurVictime()