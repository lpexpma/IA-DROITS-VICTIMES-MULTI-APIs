// app/static/app.js - VERSION COMPLÈTE
class OLIVIADroitsVictimes {
    constructor() {
        this.initializeEventListeners();
        this.testAPIsOnLoad();
    }

    initializeEventListeners() {
        document.getElementById('testApisBtn').addEventListener('click', () => this.testerAPIs());
        document.getElementById('analyzeBtn').addEventListener('click', () => this.analyserSituation());
        document.getElementById('searchBtn').addEventListener('click', () => this.rechercheComplete());
        document.getElementById('placesBtn').addEventListener('click', () => this.rechercherLieux());
        document.getElementById('clearBtn').addEventListener('click', () => this.effacerResultats());
    }

    async testerAPIs() {
        const apisStatus = document.getElementById('apisStatus');
        apisStatus.innerHTML = '<div class="api-status">⏳ Test des APIs en cours...</div>';

        try {
            const response = await fetch('/api/test-apis');
            const data = await response.json();

            let html = '';
            for (const [api, result] of Object.entries(data)) {
                const statusClass = result.status === 'success' ? 'api-success' : 'api-error';
                const emoji = result.status === 'success' ? '✅' : '❌';
                html += `<div class="api-status ${statusClass}">${emoji} ${api.toUpperCase()}: ${result.message}</div>`;
            }

            apisStatus.innerHTML = html;
        } catch (error) {
            apisStatus.innerHTML = `<div class="api-status api-error">❌ Erreur: ${error.message}</div>`;
        }
    }

    async analyserSituation() {
        const description = document.getElementById('descriptionSituation').value.trim();
        if (!description) {
            alert('Veuillez décrire votre situation');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch('/api/analyser-situation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description_situation: description,
                    code_postal: document.getElementById('codePostal').value || null
                })
            });

            if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);

            const data = await response.json();
            this.afficherAnalyseDetaillee(data);

        } catch (error) {
            this.showError(`Erreur lors de l'analyse: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async rechercheComplete() {
        const description = document.getElementById('descriptionSituation').value.trim();
        if (!description) {
            alert('Veuillez décrire votre situation');
            return;
        }

        this.showLoading();

        try {
            const apis = [];
            if (document.getElementById('apiLegifrance').checked) apis.push('legifrance');
            if (document.getElementById('apiJudilibre').checked) apis.push('judilibre');
            if (document.getElementById('apiJusticeBack').checked) apis.push('justice_back');

            const response = await fetch('/api/recherche-complete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    description_situation: description,
                    code_postal: document.getElementById('codePostal').value || null,
                    include_apis: apis
                })
            });

            if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);

            const data = await response.json();
            this.afficherResultatsComplets(data);

        } catch (error) {
            this.showError(`Erreur lors de la recherche: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    async rechercherLieux() {
        const cp = document.getElementById('codePostal').value.trim();
        if (!cp) {
            alert('Veuillez saisir un code postal');
            return;
        }

        this.showLoading();

        try {
            const response = await fetch(`/api/lieux-justice?code_postal=${cp}`);
            if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);

            const data = await response.json();
            this.afficherLieuxJustice(data);

        } catch (error) {
            this.showError(`Erreur recherche lieux: ${error.message}`);
        } finally {
            this.hideLoading();
        }
    }

    effacerResultats() {
        document.getElementById('results').innerHTML = '';
        document.getElementById('descriptionSituation').value = '';
        document.getElementById('codePostal').value = '';
    }

    showLoading() {
        document.getElementById('loading').classList.remove('hidden');
        document.getElementById('results').innerHTML = '';
    }

    hideLoading() {
        document.getElementById('loading').classList.add('hidden');
    }

    showError(message) {
        document.getElementById('results').innerHTML = `
            <div class="error-message">❌ ${message}</div>
        `;
    }

    afficherAnalyseDetaillee(data) {
        let html = '';

        // Section analyse
        html += `
            <div class="analyse-section">
                <h2 style="color: #1e40af; margin-bottom: 20px;">🧠 Analyse de Votre Situation</h2>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">${data.analyse_description.prejudices_detectes.length}</div>
                        <div class="stat-label">Types de préjudices détectés</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.analyse_description.complexite}</div>
                        <div class="stat-label">Niveau de complexité</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.analyse_description.interactions.length}</div>
                        <div class="stat-label">Interactions identifiées</div>
                    </div>
                </div>
                
                <h3 style="color: #059669; margin: 20px 0 15px 0;">📋 Préjudices Détectés :</h3>
                <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 20px;">
        `;

        data.analyse_description.prejudices_detectes.forEach(prejudice => {
            html += `<span class="prejudice-badge badge-${prejudice.categorie}">${prejudice.categorie} (${Math.round(prejudice.confiance)}%)</span>`;
        });

        html += `</div>`;

        // Interactions
        if (data.analyse_description.interactions.length > 0) {
            html += `<h3 style="color: #f59e0b; margin: 20px 0 15px 0;">⚠️ Interactions entre Préjudices :</h3>`;
            data.analyse_description.interactions.forEach(interaction => {
                html += `<div class="interaction-warning">⚠️ ${interaction}</div>`;
            });
        }

        // Estimation
        if (data.estimation_indemnisation) {
            const est = data.estimation_indemnisation.total_estime;
            const range = Math.max(1, est.max - est.min);
            const current = est.min + (range * 0.3);
            const percentage = ((current - est.min) / range) * 100;

            html += `
                <h3 style="color: #7e22ce; margin: 25px 0 15px 0;">💰 Estimation Indemnisation :</h3>
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <span>${est.min.toLocaleString()}€</span>
                        <span style="font-weight: 600; color: #1e40af;">Fourchette estimée</span>
                        <span>${est.max.toLocaleString()}€</span>
                    </div>
                    <div class="estimation-bar">
                        <div class="estimation-fill" style="width: ${percentage}%"></div>
                    </div>
                    <div style="text-align: center; color: #6b7280; font-size: 0.9em; margin-top: 10px;">
                        Estimation indicative basée sur un barème interne - expertise requise pour précision
                    </div>
                </div>
            `;
        }

        html += `</div>`;

        // Jurisprudence par préjudice
        html += `<div class="section-title">⚖️ Jurisprudence par Type de Préjudice</div>`;

        for (const [prejudice, jurisprudences] of Object.entries(data.jurisprudence_par_prejudice)) {
            if (jurisprudences.length > 0 && !jurisprudences.erreur) {
                html += `
                    <div class="result-section">
                        <h4 style="color: #374151; margin-bottom: 15px; display: flex; align-items: center; gap: 10px;">
                            <span class="prejudice-badge badge-${prejudice}">${prejudice}</span>
                            <span> - ${jurisprudences.length} décisions trouvées</span>
                        </h4>
                `;

                jurisprudences.forEach(jur => {
                    const sourceBadge = jur.source ? `<span class="prejudice-badge" style="background: #e5e7eb; color: #374151;">${jur.source.split(':')[0]}</span>` : '';
                    html += `
                        <div class="result-item">
                            <div class="result-title">${jur.titre}</div>
                            <div class="result-meta">
                                <span class="result-meta-item">🏛️ ${jur.juridiction}</span>
                                <span class="result-meta-item">📅 ${jur.date}</span>
                                <span class="result-meta-item">${jur.fiabilite}</span>
                                ${sourceBadge}
                            </div>
                            <div style="margin-bottom: 10px;"><strong>Chambre:</strong> ${jur.chambre}</div>
                            <div>${jur.resume}</div>
                        </div>
                    `;
                });

                html += `</div>`;
            }
        }

        // Recommandations
        if (data.recommandations_generales && data.recommandations_generales.length > 0) {
            html += `
                <div class="result-section">
                    <div class="section-title">🎯 Recommandations</div>
            `;

            data.recommandations_generales.forEach(reco => {
                html += `<div class="recommendation-item">✅ ${reco}</div>`;
            });

            html += `</div>`;
        }

        // Ressources locales
        if (data.ressources_locales && data.ressources_locales.lieux && data.ressources_locales.lieux.length > 0) {
            html += `
                <div class="result-section">
                    <div class="section-title">🏛️ Ressources Locales Proches</div>
            `;

            data.ressources_locales.lieux.forEach(lieu => {
                const sourceBadge = lieu.source ? `<span class="prejudice-badge" style="background: #e5e7eb; color: #374151;">${lieu.source.split(':')[0]}</span>` : '';
                html += `
                    <div class="result-item">
                        <div class="result-title">${lieu.titre}</div>
                        <div class="result-meta">
                            <span class="result-meta-item">📍 ${lieu.adresse}</span>
                            <span class="result-meta-item">📞 ${lieu.telephone}</span>
                            ${sourceBadge}
                        </div>
                        ${lieu.courriel !== 'Non renseigné' ? `<div><strong>Email:</strong> ${lieu.courriel}</div>` : ''}
                        ${lieu.horaire !== 'Non renseigné' ? `<div><strong>Horaires:</strong> ${lieu.horaire}</div>` : ''}
                    </div>
                `;
            });

            html += `</div>`;
        }

        document.getElementById('results').innerHTML = html;
    }

    afficherResultatsComplets(data) {
        let html = '<div class="section-title">🔍 Résultats de la Recherche Multi-APIs</div>';

        // Statistiques
        if (data.analyse) {
            html += `
                <div class="stats-grid">
                    ${data.analyse.nombre_textes ? `<div class="stat-card"><div class="stat-number">${data.analyse.nombre_textes}</div><div class="stat-label">Textes Législatifs</div></div>` : ''}
                    ${data.analyse.nombre_jurisprudence ? `<div class="stat-card"><div class="stat-number">${data.analyse.nombre_jurisprudence}</div><div class="stat-label">Jurisprudences</div></div>` : ''}
                    ${data.analyse.nombre_lieux ? `<div class="stat-card"><div class="stat-number">${data.analyse.nombre_lieux}</div><div class="stat-label">Lieux de Justice</div></div>` : ''}
                </div>
            `;
        }

        // Légifrance
        if (data.legifrance && data.legifrance.length > 0) {
            html += `
                <div class="result-section">
                    <div class="section-title">📚 Textes Légifrance</div>
                    ${data.legifrance.map(item => `
                        <div class="result-item">
                            <div class="result-title">${item.titre}</div>
                            <div class="result-meta">
                                <span class="result-meta-item">📄 ${item.nature}</span>
                                <span class="result-meta-item">📅 ${item.date}</span>
                            </div>
                            <div>${item.resume}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Judilibre
        if (data.judilibre && data.judilibre.length > 0) {
            html += `
                <div class="result-section">
                    <div class="section-title">⚖️ Jurisprudence Judilibre</div>
                    ${data.judilibre.map(item => `
                        <div class="result-item">
                            <div class="result-title">${item.titre}</div>
                            <div class="result-meta">
                                <span class="result-meta-item">🏛️ ${item.juridiction}</span>
                                <span class="result-meta-item">📅 ${item.date}</span>
                                <span class="result-meta-item">${item.fiabilite}</span>
                            </div>
                            <div style="margin-bottom: 10px;"><strong>Chambre:</strong> ${item.chambre}</div>
                            <div>${item.resume}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Justice Back
        if (data.justice_back && data.justice_back.length > 0) {
            html += `
                <div class="result-section">
                    <div class="section-title">🏛️ Lieux de Justice</div>
                    ${data.justice_back.map(item => `
                        <div class="result-item">
                            <div class="result-title">${item.titre}</div>
                            <div class="result-meta">
                                <span class="result-meta-item">📍 ${item.adresse}</span>
                                <span class="result-meta-item">📞 ${item.telephone}</span>
                            </div>
                            ${item.courriel !== 'Non renseigné' ? `<div><strong>Email:</strong> ${item.courriel}</div>` : ''}
                        </div>
                    `).join('')}
                </div>
            `;
        }

        document.getElementById('results').innerHTML = html;
    }

    afficherLieuxJustice(data) {
        let html = `
            <div class="result-section">
                <div class="section-title">🏛️ Lieux de Justice (${data.total} résultats)</div>
        `;

        if (data.lieux && data.lieux.length > 0) {
            data.lieux.forEach(lieu => {
                html += `
                    <div class="result-item">
                        <div class="result-title">${lieu.titre}</div>
                        <div class="result-meta">
                            <span class="result-meta-item">📍 ${lieu.adresse}</span>
                            <span class="result-meta-item">📞 ${lieu.telephone}</span>
                        </div>
                        ${lieu.courriel !== 'Non renseigné' ? `<div><strong>Email:</strong> ${lieu.courriel}</div>` : ''}
                        ${lieu.horaire !== 'Non renseigné' ? `<div><strong>Horaires:</strong> ${lieu.horaire}</div>` : ''}
                    </div>
                `;
            });
        } else {
            html += '<p style="text-align: center; color: #6b7280; padding: 20px;">Aucun lieu de justice trouvé pour ce code postal.</p>';
        }

        html += '</div>';
        document.getElementById('results').innerHTML = html;
    }

    testAPIsOnLoad() {
        this.testerAPIs();
    }
}

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    new OLIVIADroitsVictimes();
});