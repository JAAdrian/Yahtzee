(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

        var scoreSheet = document.querySelector('.score-sheet');
        if (!scoreSheet) return;

        var gameMatch = window.location.pathname.match(/^\/games\/(\d+)\/score\//);
        var gamePk = gameMatch ? gameMatch[1] : null;

        var debounceTimer = null;

        function sendScore(el) {
            if (!el.dataset.gamePlayer || !el.dataset.category) return;

            var gpId = el.dataset.gamePlayer;
            var category = el.dataset.category;
            var namePrefix = el.tagName === 'SELECT' ? 'state_' : 'score_';

            var formData = new FormData();
            formData.append('game_player_id', gpId);
            formData.append('category', category);
            formData.append(namePrefix + gpId + '_' + category, el.value);

            if (!gamePk) return;

            var url = '/games/' + gamePk + '/score-partial/';

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            }).then(function(response) {
                if (!response.ok) return null;
                return response.text();
            }).then(function(html) {
                if (!html) return;

                var upperDest = document.getElementById('upper-totals');
                var lowerDest = document.getElementById('lower-totals');
                if (!upperDest || !lowerDest) return;

                var upperMatch = html.match(/<tbody id="__upper__">([\s\S]*?)<\/tbody>/);
                var lowerMatch = html.match(/<tbody id="__lower__">([\s\S]*?)<\/tbody>/);

                if (upperMatch) {
                    var tmp = document.createElement('div');
                    tmp.innerHTML = '<table><tbody>' + upperMatch[1] + '</tbody></table>';
                    var rows = tmp.querySelectorAll('tr');
                    upperDest.innerHTML = '';
                    rows.forEach(function(row) { upperDest.appendChild(row.cloneNode(true)); });
                }

                if (lowerMatch) {
                    var tmp = document.createElement('div');
                    tmp.innerHTML = '<table><tbody>' + lowerMatch[1] + '</tbody></table>';
                    var rows = tmp.querySelectorAll('tr');
                    lowerDest.innerHTML = '';
                    rows.forEach(function(row) { lowerDest.appendChild(row.cloneNode(true)); });
                }
            }).catch(function(err) {
                console.error('[score] error:', err);
            });
        }

        scoreSheet.addEventListener('input', function(e) {
            var el = e.target;
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                sendScore(el);
            }, 300);
        });

        scoreSheet.addEventListener('change', function(e) {
            var el = e.target;
            clearTimeout(debounceTimer);
            sendScore(el);
        });
    });
})();
