<script>
    import NavBar from "./NavBar.svelte";
    import AutoPage from "./AutoPage.svelte";
    import LoginPage from "./LoginPage.svelte";
    import ClimbSection from "./ClimbSection.svelte";
</script>

<main>
    <div><NavBar /></div>
    <div class="line"><AutoPage /></div>
    <div class="line"><ClimbSection /></div>
    <div class="filler" />
    <!-- <LoginPage /> -->
</main>

<style>
    main {
        background-color: rgb(50, 50, 50);
        overflow: hidden;
    }

    .line {
        display: inline-block;
    }

    .filler {
        padding-top: 1000px;
    }
</style>
