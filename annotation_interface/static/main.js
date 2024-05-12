const confirmBtn = document.getElementById("correct");
const deleteBtn = document.getElementById("delete");
const darkenStyle = "#555 linear-gradient(90deg, rgba(22, 248, 2, 0.00) 0%, rgba(22, 248, 2, 0.50) 93%, rgba(22, 248, 2, 0.50) 100%";

function updateDisplay(data) {
    console.log(data);
    if (data.label === null || data.label === "") {
        data.label = "<NO LABEL>";
    }
    document.querySelector(".sentence-display").textContent = data.sentence;
    document.querySelector(".label-display").textContent = data.label;
    document.querySelector(".progress-read").textContent = `${data.labeled_rows} labeled`;
    document.querySelector(".progress-bar").style.width = data.progress;    
}

function fetchDataAndUpdateDisplay_get(endpoint) {
    fetch(endpoint)
        .then(response => response.json())
        .then(data => updateDisplay(data));
}

function fetchDataAndUpdateDisplay_update(event, action) {
    let label = "";
    if (action === "update") {
        action = "update";
        label = document.querySelector(`#${event.key} > .label`).textContent;
        label = label.replace(/[^a-zA-Z\/]/g, "");
    }

    let data = {
        action: action,
        label: label
    };

    fetch("/label/update", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
    .then(response => response.json())
    .then(data => updateDisplay(data))
    .catch((error) => {
        console.error("Error: ", error);
    })
}

window.onload = function() {
    fetchDataAndUpdateDisplay_get("/label")
}

window.addEventListener("keydown", function(event) {
    if (event.target.tagName === "INPUT") {
        return;
    }
    console.log("key pressed!")
    if (event.key === ' ') {
        confirmBtn.classList.add('pressed');
        fetchDataAndUpdateDisplay_update(event, "correct")
    }
    else if (event.key === 'Delete') {
        deleteBtn.classList.add('pressed');
        fetchDataAndUpdateDisplay_update(event, "delete")
    }
    else if (event.ctrlKey && event.key === "z"){
        fetch("/label/undo")
            .then(response => response.json())
            .then(data => updateDisplay(data))
            .catch((error) => {
                console.error("Error: ", error);
            })
    } else {
        console.log(event.key)
        let miscBtn = document.getElementById(event.key);  // Jinja configured to allow this
        if (miscBtn === null) { return; }

        fetchDataAndUpdateDisplay_update(event, "update")
        miscBtn.classList.add('pressed');
    }
})

window.addEventListener("keyup", function(event) {
    if (event.target.tagName === "INPUT") {
        return;
    }
    if (event.key === ' ') {
        confirmBtn.classList.remove('pressed');
    }
    else if (event.key === 'Delete') {
        deleteBtn.classList.remove('pressed');
    }
    else {
        let miscBtn = document.getElementById(event.key);  // Jinja configured to allow this
        if (miscBtn === null) { return; }
        miscBtn.classList.remove('pressed');
    }
})

document.getElementById("myForm").addEventListener("submit", function(event) {
    event.preventDefault(); 

    let inputElement = document.getElementById("text-box0")
    let inputValue = inputElement.value.toUpperCase();

    fetch("/label/update", { // replace '/your-endpoint' with your actual endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            action: "update",
            label: inputValue
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);
        updateDisplay(data);

        // Reset input element
        inputElement.value = "";
        // inputElement.blur();
    })
    .catch((error) => {
        console.error("Error: ", error);
    })
});