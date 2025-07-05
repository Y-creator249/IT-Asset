odoo.define('it_asset_management.portal', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.ITPortalManagement = publicWidget.Widget.extend({
        selector: '.o_portal_it_management',
        events: {
            'click .incident-filters button': '_onFilterClick',
            'input .o_portal_search_panel input': '_onSearch',
            'change select[name="equipment_id"]': '_onEquipmentChange',
            'submit .incident-form': '_onIncidentSubmit',
            'change input[type="file"]': '_onFileChange',
            'click .o_portal_attachment_delete': '_onAttachmentDelete',
            'click .o_portal_attachment_preview': '_onAttachmentPreview'
        },

        init: function () {
            this._super.apply(this, arguments);
            this.maxFileSize = 25 * 1024 * 1024; // 25MB
            this._pendingRpcs = []; // Track pending RPC calls
        },

        start: function () {
            var def = this._super.apply(this, arguments);
            this._initializeDatePickers();
            this._initializeTooltips();
            return def;
        },

        destroy: function () {
            // Clean up datepickers
            this.$('.o_datepicker').each(function () {
                var $el = $(this);
                if ($el.data('datepicker')) {
                    $el.datepicker('destroy');
                }
            });

            // Clean up tooltips
            this.$('[data-toggle="tooltip"]').each(function () {
                var $el = $(this);
                if ($el.data('bs.tooltip')) {
                    $el.tooltip('dispose');
                }
            });

            // Abort pending RPC calls
            this._pendingRpcs.forEach(function (rpc) {
                if (rpc && typeof rpc.abort === 'function') {
                    rpc.abort();
                }
            });
            this._pendingRpcs = [];

            // Remove dynamically added DOM elements (e.g., modals)
            this.$('.modal').modal('hide').remove();

            // Remove event listeners (handled by Odoo's Widget, but ensure manual ones are cleaned)
            this.$el.off();

            // Call parent destroy
            this._super.apply(this, arguments);
        },

        _initializeDatePickers: function () {
            this.$('.o_datepicker').datepicker({
                format: 'dd/mm/yyyy',
                autoclose: true,
                todayHighlight: true
            });
        },

        _initializeTooltips: function () {
            this.$('[data-toggle="tooltip"]').tooltip();
        },

        _onFilterClick: function (ev) {
            var $button = $(ev.currentTarget);
            var filter = $button.data('filter');
            
            this.$('.incident-filters button').removeClass('active');
            $button.addClass('active');
            
            if (filter === 'all') {
                this.$('tr[data-incident]').show();
            } else {
                this.$('tr[data-incident]').hide();
                this.$('tr[data-incident="' + filter + '"]').show();
            }
        },

        _onSearch: function (ev) {
            var value = $(ev.currentTarget).val().toLowerCase();
            var $rows = this.$('table tbody tr');
            var $noResult = this.$('.no-result');

            var hasVisibleRows = false;
            $rows.each(function() {
                var $row = $(this);
                var text = $row.text().toLowerCase();
                var isVisible = text.indexOf(value) > -1;
                $row.toggle(isVisible);
                if (isVisible) hasVisibleRows = true;
            });

            $noResult.toggle(!hasVisibleRows);
        },

        _onEquipmentChange: function (ev) {
            var self = this;
            var equipmentId = $(ev.currentTarget).val();
            
            if (equipmentId) {
                var rpc = this._rpc({
                    route: '/my/equipment/' + equipmentId + '/info',
                    params: {}
                }).then(function (result) {
                    if (result.error) {
                        self.displayNotification({
                            type: 'warning',
                            title: _t('Erreur'),
                            message: result.error
                        });
                        return;
                    }
                    self._updateEquipmentInfo(result);
                });
                this._pendingRpcs.push(rpc); // Track RPC
            }
        },

        _updateEquipmentInfo: function (data) {
            var $infoPanel = this.$('.equipment-info');
            if (data.warranty_end) {
                var warningClass = this._getWarrantyWarningClass(data.warranty_end);
                $infoPanel.find('.warranty-status').removeClass().addClass('warranty-status ' + warningClass);
            }
            $infoPanel.find('.equipment-details').html(data.details_html);
        },

        _getWarrantyWarningClass: function (warrantyEnd) {
            var today = new Date();
            var endDate = new Date(warrantyEnd);
            var diffDays = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
            
            if (diffDays < 0) return 'text-danger';
            if (diffDays < 30) return 'text-warning';
            return 'text-success';
        },

        _onIncidentSubmit: function (ev) {
            var $form = $(ev.currentTarget);
            var $description = $form.find('textarea[name="description"]');
            
            if (!$description.val().trim()) {
                ev.preventDefault();
                this.displayNotification({
                    type: 'warning',
                    title: _t('Attention'),
                    message: _t('Veuillez fournir une description de l\'incident.')
                });
                $description.focus();
                return false;
            }
        },

        _onFileChange: function (ev) {
            var file = ev.target.files[0];
            var $fileInput = $(ev.target);
            
            if (file && file.size > this.maxFileSize) {
                this.displayNotification({
                    type: 'warning',
                    title: _t('Fichier trop volumineux'),
                    message: _t('La taille du fichier ne doit pas dépasser 25MB.')
                });
                $fileInput.val('');
            }
        },

        _onAttachmentDelete: function (ev) {
            ev.preventDefault();
            var self = this;
            var $link = $(ev.currentTarget);
            var attachmentId = $link.data('id');

            if (confirm(_t("Voulez-vous vraiment supprimer cette pièce jointe ?"))) {
                var rpc = this._rpc({
                    route: '/my/attachment/delete',
                    params: {
                        attachment_id: attachmentId
                    }
                }).then(function (result) {
                    if (result.success) {
                        $link.closest('.o_portal_attachment').remove();
                        self.displayNotification({
                            type: 'success',
                            message: _t("Pièce jointe supprimée avec succès")
                        });
                    } else {
                        self.displayNotification({
                            type: 'warning',
                            message: result.error || _t("Erreur lors de la suppression")
                        });
                    }
                });
                this._pendingRpcs.push(rpc); // Track RPC
            }
        },

        _onAttachmentPreview: function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var attachmentUrl = $link.attr('href');
            var filename = $link.data('filename');

            var $modal = $(qweb.render('portal.AttachmentPreviewModal', {
                url: attachmentUrl,
                filename: filename
            }));
            $modal.modal('show');
            // Ensure modal is cleaned up when hidden
            $modal.on('hidden.bs.modal', function () {
                $modal.remove();
            });
        },

        _updateAttachmentList: function (attachments) {
            var $attachmentList = this.$('.o_portal_attachments_list');
            $attachmentList.empty();

            _.each(attachments, function (attachment) {
                var $attachment = $(qweb.render('portal.AttachmentItem', {
                    attachment: attachment
                }));
                $attachmentList.append($attachment);
            });
        }
    });

    return publicWidget.registry.ITPortalManagement;
});