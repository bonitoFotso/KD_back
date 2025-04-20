/* js/admin/opportunite.js */

(function($) {
    $(document).ready(function() {
        // Créer et insérer le tableau de bord des opportunités
        if ($('.model-opportunite.changelist-view').length) {
            createOpportunityDashboard();
        }

        // Configurer les confirmations pour les actions critiques
        setupActionConfirmations();

        // Ajouter un indicateur de probabilité visuel
        enhanceProbabilityDisplay();

        // Mettre en évidence les dates de relance en retard
        highlightOverdueRelances();

        // Améliorer l'expérience utilisateur lors de la création/modification d'opportunités
        enhanceOpportunityForm();
    });

    /**
     * Crée un tableau de bord statistique au-dessus de la liste des opportunités
     */
    function createOpportunityDashboard() {
        // Récupérer les données de contexte (supposées définies par Python)
        var summaryStats = JSON.parse(document.getElementById('summary-stats-data').textContent || '{}');
        var statusCounts = JSON.parse(document.getElementById('status-counts-data').textContent || '{}');
        
        if (!summaryStats || !statusCounts) return;

        // Créer le conteneur du tableau de bord
        var dashboard = $('<div class="opportunity-dashboard"></div>');
        var header = $('<div class="opportunity-dashboard-header">Tableau de bord des opportunités</div>');
        dashboard.append(header);

        // Ajouter les cartes de statistiques
        var totalCard = createStatCard('Montant total', formatCurrency(summaryStats.total_montant));
        var estimatedCard = createStatCard('Montant estimé', formatCurrency(summaryStats.total_estime));
        var weightedCard = createStatCard('Valeur pondérée', formatCurrency(summaryStats.total_pondere));
        
        dashboard.append(totalCard, estimatedCard, weightedCard);
        
        // Ajouter les badges de statut
        var statusBadgesContainer = $('<div class="status-badges"></div>');
        
        for (var status in statusCounts) {
            var statusData = statusCounts[status];
            var badge = $('<div class="status-badge status-' + status + '"></div>');
            badge.append('<span class="status-badge-count">' + statusData.count + '</span>');
            badge.append('<span class="status-badge-label">' + statusData.label + '</span>');
            statusBadgesContainer.append(badge);
        }
        
        dashboard.append(statusBadgesContainer);
        
        // Insérer le tableau de bord avant le résultat
        $('.results').before(dashboard);
    }

    /**
     * Crée une carte de statistique pour le tableau de bord
     */
    function createStatCard(title, value) {
        var card = $('<div class="stat-card"></div>');
        card.append('<div class="stat-card-title">' + title + '</div>');
        card.append('<div class="stat-card-value">' + value + '</div>');
        return card;
    }

    /**
     * Configure des confirmations pour les actions critiques
     */
    function setupActionConfirmations() {
        // Confirmation pour la suppression
        $('input[name="action"]').change(function() {
            var selectedAction = $(this).val();
            
            if (selectedAction === 'delete_selected') {
                $(this).closest('form').on('submit', function(e) {
                    return confirm("Êtes-vous sûr de vouloir supprimer les opportunités sélectionnées ? Cette action est irréversible.");
                });
            }
            
            if (selectedAction === 'mark_as_lost') {
                $(this).closest('form').on('submit', function(e) {
                    return confirm("Êtes-vous sûr de vouloir marquer ces opportunités comme perdues ?");
                });
            }
        });
    }

    /**
     * Ajoute un indicateur visuel pour le pourcentage de probabilité
     */
    function enhanceProbabilityDisplay() {
        $('.field-probabilite_display').each(function() {
            var probabilityText = $(this).text();
            var probabilityValue = parseInt(probabilityText.replace('%', '').trim());
            
            var indicator = $('<div class="probabilite-indicator"></div>');
            var bar = $('<div class="probabilite-indicator-bar"></div>').css('width', probabilityValue + '%');
            
            indicator.append(bar);
            $(this).append(indicator);
        });
    }

    /**
     * Met en évidence les dates de relance dépassées
     */
    function highlightOverdueRelances() {
        // Dans le formulaire de détail
        var today = new Date();
        today.setHours(0, 0, 0, 0);
        
        $('.field-box.field-relance').each(function() {
            var relanceInput = $(this).find('input[type="date"], input.vDateField');
            if (relanceInput.length) {
                var relanceDate = new Date(relanceInput.val());
                if (relanceDate < today) {
                    $(this).addClass('overdue');
                }
            }
        });
    }

    /**
     * Améliore le formulaire d'édition d'opportunité
     */
    function enhanceOpportunityForm() {
        // Mettre à jour automatiquement la probabilité en fonction du statut
        $('#id_statut').change(function() {
            var statut = $(this).val();
            var probabilites = {
                'PROSPECT': 10,
                'QUALIFICATION': 30,
                'PROPOSITION': 50,
                'NEGOCIATION': 75,
                'GAGNEE': 100,
                'PERDUE': 0
            };
            
            if (statut in probabilites) {
                $('#id_probabilite').val(probabilites[statut]);
            }
        });
        
        // Mettre à jour la valeur pondérée lorsque les champs sont modifiés
        $('#id_montant_estime, #id_probabilite').change(function() {
            var montant = parseFloat($('#id_montant_estime').val()) || 0;
            var probabilite = parseFloat($('#id_probabilite').val()) || 0;
            var valeurPonderee = montant * probabilite / 100;
            
            $('.field-valeur_ponderee_display').text(formatCurrency(valeurPonderee));
        });
    }

    /**
     * Formate un nombre en devise
     */
    function formatCurrency(value) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }

})(django.jQuery);