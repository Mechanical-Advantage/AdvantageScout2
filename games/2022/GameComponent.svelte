<script>
    import NavBar from "./NavBar.svelte";
    import AutoPage from "./AutoPage.svelte";
    import LoginPage from "./LoginPage.svelte";
    import ClimbSection from "./ClimbSection.svelte";
    import EndGamePage from "./EndGamePage.svelte";
</script>

<main>
    <div class="navbar"><NavBar /></div>
    <!-- <div class="line"><AutoPage /></div>
    <div class="line"><ClimbSection /></div>  -->
    <div class="filler" />

    <!--<LoginPage /> -->

    <div class="end"><EndGamePage /></div>
</main>

<style>
    main {
        background-color: rgb(50, 50, 50);
        overflow: hidden;
    }

    .line {
        display: inline-block;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }

    .filler {
        padding-top: 1000px;
    }

    .navbar {
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
</style>
