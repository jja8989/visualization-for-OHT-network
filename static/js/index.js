window.onload=function(){
    
    const init_btn = $('#init-btn')

    init_btn.addEventListener('click', (e)=>{
        document.querySelectorAll('input[type="radio"]').forEach(input=>{
            input.checked = false;
        })

        document.querySelectorAll('input[type="file"]').forEach(input=>{
            input.value = "";
        })

        document.querySelectorAll('input[type="text"]').forEach(input=>{
            input.value = "";
        })

        document.querySelectorAll('.sel-file').forEach(input=>{
            input.setAttribute('data-from', "")
        })

        $(".port").style.display = 'none';
        $(".flow").style.display = 'none';
        $(".download").style.display = 'none';
        $(".graph-section").innerHTML = "";
        $(".centrality").style.display = 'none';
    })

    $("#toggle-json").addEventListener('click', (e)=>{
        init_btn.click()
        $(".existing-json").style.display = 'block';
        $(".new-cal").style.display = 'none';
    })

    $("#toggle-calculation").addEventListener('click', (e)=>{
        init_btn.click()
        $(".existing-json").style.display = 'none';
        $(".new-cal").style.display = 'block';
    })

    //file add trigers
    const load_btns = document.querySelectorAll('.load_btn');
    const add_btns = document.querySelectorAll('.add_btn');
    const file_btns = document.querySelectorAll('input[type="file"]');
    const sel_inputs = document.querySelectorAll('input.sel-file');

    for(let i=0; i<add_btns.length; i++){
        add_btns[i].addEventListener('click', (e)=>{
            file_btns[i].click();
        })
        file_btns[i].addEventListener('change', function(e){
            sel_inputs[i].value = this.files[0].name;
            sel_inputs[i].setAttribute('data-from', 'file')
        })
    }


    //port display
    document.querySelectorAll('.structure input[type="radio"]').forEach(radio=>{
        radio.addEventListener('change', (e)=>{
            if(e.target.value == 'node-port'){
                $(".port").style.display = 'block';
                $(".flow").style.display = 'none';
                $(".centrality").style.display = 'block';
            }
            else if(e.target.value == 'flow'){
                $(".flow").style.display = 'block';
                $(".port").style.display = 'none';
                $(".centrality").style.display = 'none';

            }
            else if(e.target.value == 'node'){
                $(".flow").style.display = 'none';
                $(".port").style.display = 'none';
                $(".centrality").style.display = 'block';

            }
            else{
                $(".port").style.display = 'none';
                $(".flow").style.display = 'none';
                $(".centrality").style.display = 'none';
            }
        })
    })

    const modal  = $('.modal');

    document.querySelectorAll('.load_btn').forEach(load=>{
        load.addEventListener('click', (e)=>{
            const current = e.target;
            modal.style.display = "block";

            switch(current.dataset.ref){
                case "json":
                    $(".collections").innerHTML=`
                    <h2>JSON List in DB</h2>
                    `
                    get_docs('json')
                    break;
                case "node":
                    $(".collections").innerHTML=`
                    <h2>Node List in DB</h2>
                    `
                    get_docs('node')
                    break;
                case "link":
                    $(".collections").innerHTML=`
                    <h2>Link List in DB</h2>
                    `
                    get_docs('link')
                    break;
                case "port":
                    $(".collections").innerHTML=`
                    <h2>Port List in DB</h2>
                    `
                    get_docs('port')
                    break;
                case "flow":
                    $(".collections").innerHTML=`
                    <h2>Flow List in DB</h2>
                    `
                    get_docs('flow')
                    break;
            }
        })
    })

    $('#close').onclick = (e)=>{
        modal.style.display = "none";
    }

    window.onclick = (e) => {
        if(e.target == modal){
            modal.style.display = "none";
        }
    }

    let graphData = null;

    document.addEventListener('keydown', function(e) {
        var isEscape = false;
        if ("key" in e) {
            isEscape = (e.key === "Escape" || e.key === "Esc");
        } else {
            isEscape = (e.keyCode === 27);
        }
        if (isEscape && modal.style.display === 'block') {
            modal.style.display = 'none';
        }
    });

    $('#submit_btn').onclick=(e)=>{
        const formData = new FormData();

        for(let i=0; i<sel_inputs.length; i++){
            if (sel_inputs[i].value != ""){
                if(sel_inputs[i].dataset.from == 'file'){
                    formData.append(file_btns[i].name,file_btns[i].files[0])
                }else{
                    formData.append(load_btns[i].dataset.ref, sel_inputs[i].value)
                }
            }
        }


        let structure = $('input[name="structure"]:checked');
        let centrality = $('input[name="centrality"]:checked');

        if (structure){
            formData.append('structure', structure.value);
        }
        if (centrality){
            formData.append('centrality', centrality.value);
        }

        formData.append('save_name', $('#save-name').value);

        

        fetch('/upload', {
            method : 'POST',
            body : formData,
        })
        .then(response => response.json())
        .then(data=>{
            $(".graph-section").innerHTML = "";
            $("#init-btn").click();
            graphData = JSON.parse(JSON.stringify(data)); 
            draw(data.data, data.type)

            $('.download').style.display = 'block';
        })
    }

    $('.download').addEventListener('click', function() {
        if (graphData.data && graphData.type != "flow") {
            var nodesCSV = sortAndConvertToCSV(graphData.data.nodes, graphData.type, ['id', graphData.type]);
            downloadCSV(nodesCSV, `${graphData.name}_node_data.csv`, function() {
                var edgesCSV = sortAndConvertToCSV(graphData.data.links, graphData.type, ['source', 'target', graphData.type]);
                downloadCSV(edgesCSV, `${graphData.name}_edge_data.csv`);
            });
        }
        else if(graphData.data && graphData.type == 'flow'){
            var edgesCSV = sortAndConvertToCSV(graphData.data.links, graphData.type, ['source', 'target', graphData.type]);
                downloadCSV(edgesCSV, `${graphData.name}_flow_data.csv`);
        }
    });



}

function $(selector){
    return document.querySelector(selector)
}

function get_docs(col){
    fetch(`docs/${col}`)
    .then(response => response.json())
    .then(data => {
        $('.docs ul').innerHTML = ""
        data.forEach(doc => {
            var item = document.createElement('li');
            item.textContent = doc.name;
            $('.docs ul').appendChild(item);

            item.addEventListener("click", function() {
                let selectedItem = this.textContent;
                $(`input[name="${col}-name"]`).value = selectedItem;
                $(".modal").style.display = "none";
              });
        })
        if (data.length == 0){
            $('.docs ul').style.border = 'none';
        }
    })   
}


function sortAndConvertToCSV(data, sortAttribute, columnOrder, excludeKeys = []) {
    let sortedData = data.sort((a, b) => {
        let aValue = a[sortAttribute] !== undefined ? a[sortAttribute] : 0;
        let bValue = b[sortAttribute] !== undefined ? b[sortAttribute] : 0;
        return bValue - aValue;
    });

    let filteredData = sortedData.map(item => {
        let newItem = {};
        for (let key in item) {
            if (!excludeKeys.includes(key)) {
                newItem[key] = item[key];
            }
        }
        return newItem;
    });

    return d3.csvFormat(filteredData, columnOrder);
}


function downloadCSV(csvData, filename, callback) {
    var blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
    var link = document.createElement("a");
    if (link.download !== undefined) {
        var url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        if (callback) {
            setTimeout(callback, 100);
        }
    }
}
