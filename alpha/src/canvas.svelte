<!-- <script>

import { onMount } from 'svelte';

let canvas;



const drawField = (ctx) => {

    // draw field boundary
    ctx.beginPath();
    ctx.rect(5, 5, 1200, 600);
    ctx.lineWidth = 10;
    ctx.fillStyle = "grey";
    ctx.fill();
    ctx.stroke();

    // draw red thing
    ctx.beginPath();
    ctx.rect(450, 500, 300, 100);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "red";
    ctx.stroke();

    // draw blue thing
    ctx.beginPath();
    ctx.rect(450, 10, 300, 100);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "blue";
    ctx.stroke();

    // draw center square
    ctx.beginPath();
    ctx.translate(-50,350);
    ctx.rotate( -1 * 30 * Math.PI / 180);
    ctx.rect(450,150,280,280);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "black";
    ctx.stroke();

    ctx.rotate(30 * Math.PI / 180)
    ctx.translate(50,-350)

    //draw lines
    ctx.beginPath();
    ctx.moveTo(250,10);
    ctx.lineTo(250,600);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "white";
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(950,10);
    ctx.lineTo(950,600);
    ctx.lineWidth = 3;
    ctx.strokeStyle = "white";
    ctx.stroke();
}



onMount(() => {
    const context = canvas.getContext('2d')
    canvas.width = 1210;
    canvas.height = 610;
    drawField(context);
});

</script>

<canvas bind:this={canvas} />

<style>
    canvas {

        padding-left: 0;
        padding-right: 0;
        padding-top: 150px;
        margin-left: auto;
        margin-right: auto;
        display: block;
        

    }

   

</style> -->
