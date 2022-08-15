<!-- <script>


let dict = {

    UpperSuccessCount: 0,
    UpperFailCount: 0,
}


const clicked = () => {
    dict.UpperSuccessCount +=1;
}

</script>

<main>

    <button on:click={clicked} id="UpperSuccessbutton" class="success">{dict["UpperSuccessCount"]}</button>

    <button on:click={clicked} id="UpperFailurebutton" class="warning">{dict["UpperFailCount"]}</button>

</main>

<style>

#UpperSuccessbutton {
  position:absolute;
  left:100px;
  top:200px;
  background-color: #4CAF50;
  font-size: 50px;
  padding: 15px;
  border-color: black;
  border-width: 5px;

}

#UpperFailurebutton {
  position:absolute;
  left:200px;
  top:200px;
  background-color: #f44336;
  font-size: 50px;
  padding: 15px;
  border-color: black;
  border-width: 5px;

}

</style> -->