var dmcfuncs = window.dashMantineFunctions = window.dashMantineFunctions || {};

dmcfuncs.disableInvalidRange = function(dateStr, opts) {
    const date = dayjs(dateStr, "YYYY-MM-DD");
    const startDate = dayjs(opts.startDate, "YYYY-MM-DD");
    const endDate = dayjs(opts.endDate, "YYYY-MM-DD")
    const validDurationsRaw = opts.validDurations || [];

    // Par défaut on ne désactive rien
    let disable = false

    // Si seule la date de début de la range est choisie
    // on désactive tout sauf les durées permises
    if (startDate.isValid() && !endDate.isValid()) {
        const diff = date.diff(startDate, 'day');

        // Soustraire 1 à chaque durée reçue (e.g 1 jour => diff de 0)
        const validDurations = validDurationsRaw.map(d => d-1);

        disable = !validDurations.includes(diff)
    }

    // return true si la date doit être désactivée dans le calendrier
    return disable

};