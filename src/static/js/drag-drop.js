document.addEventListener('DOMContentLoaded', function() {
    const icons = document.querySelectorAll('.font-awesome-icon');
    const canvas = document.getElementById('simulation');

    let draggedIcon = null;

    icons.forEach(icon => {
        icon.addEventListener('mousedown', startDrag);
    });

    canvas.addEventListener('mouseup', endDrag);
    canvas.addEventListener('mousemove', drag);

    function startDrag(event) {
        event.stopPropagation();
        draggedIcon = this;
    }

    function endDrag() {
        draggedIcon = null;
    }

    function drag(event) {
        if (draggedIcon) {
            const rect = canvas.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            draggedIcon.style.position = 'absolute';
            draggedIcon.style.left = `${x}px`;
            draggedIcon.style.top = `${y}px`;
        }
    }

    // Example: Create icons on the canvas
    function createIcon(x, y) {
        const icon = document.createElement('span');
        icon.className = 'font-awesome-icon fas fa-camera';
        icon.style.left = `${x}px`;
        icon.style.top = `${y}px`;
        canvas.appendChild(icon);
    }

    // Example: Create icons on the canvas at specific positions
    createIcon(50, 50);
    createIcon(150, 150);
});
