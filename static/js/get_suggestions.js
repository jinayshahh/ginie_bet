    $(document).ready(function() {
    const input = $('#user_name');
    const datalist = $('#user_names');

    input.on('input', function() {
        const inputValue = input.val();
        datalist.empty();

        if (inputValue.length > 0) {
            $.get(`/get_suggestions/${inputValue}`, function(data) {
                data.forEach(function(option) {
                    datalist.append(`<option value="${option}">`);
                });
            });
        }
    });
});