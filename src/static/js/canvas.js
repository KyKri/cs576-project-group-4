function getCanvasDetails(){
    const canvas = document.getElementById('simulation');
    const rect = canvas.getBoundingClientRect();
    const xOffset = rect.left;
    const yOffset = rect.top;

    return { canvas, xOffset, yOffset };
}

function getElementDetails(element){
    const xElement = element.getBoundingClientRect().x;
    const yElement = element.getBoundingClientRect().y;
    const widthOffset = (element.getBoundingClientRect().width)/2
    const heightOffset = (element.getBoundingClientRect().height)/2 

    return { xElement, yElement, widthOffset, heightOffset };
}

function drawCircle(x, y, r){
    const canvas = document.getElementById('simulation');
    const ctx = canvas.getContext("2d");

    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.strokeStyle = "white";
    ctx.stroke();
    return [x, y];
}

function updateCanvas(){
    const { canvas, xOffset, yOffset } = getCanvasDetails();
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    //select only base stations
    baseStationsOnCanvas = $('.font-awesome-icon.fa-tower-cell').filter(function(){
        return $(this).css('position') === 'absolute';
    });
    //select only end users
    endUsersOnCanvas = $('.font-awesome-icon.fa-mobile').filter(function(){
        return $(this).css('position') === 'absolute';
    });

    //draw ranges for all base stations
    baseStationsOnCanvas.each(function(index, element){
        const { xElement, yElement, widthOffset, heightOffset } = getElementDetails(element);

        //API CALL NEEDED: get actual range of each base station
        drawCircle((xElement - xOffset + widthOffset), (yElement - yOffset + heightOffset), 80);
    });

    //draw lines connectiong end users connecting to every base station within range
    endUsersOnCanvas.each(function(i, element1){
        const user = getElementDetails(element1);
        const xUser = user.xElement - xOffset + user.widthOffset;
        const yUser = user.yElement - yOffset + user.heightOffset;
        baseStationsOnCanvas.each(function(j, element2){
            const station = getElementDetails(element2);
            const xStation = station.xElement - xOffset + station.widthOffset;
            const yStation = station.yElement - yOffset + station.heightOffset;

            const distance = Math.hypot(xUser - xStation, yUser - yStation);
            //once again, need API call to get actual range of each base station
            if (distance <= 80){
                ctx.strokeStyle = "red";
                ctx.beginPath();
                ctx.moveTo(xUser, yUser);
                ctx.lineTo(xStation, yStation);
                ctx.stroke();
            }
        })
    });
}

