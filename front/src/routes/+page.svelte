<script lang="ts">

    let url = "http://192.168.1.98:5400/stream/"

    let users = [
        "justketh",
        "cooksux"
    ]

    let imagesUrl = []

    let currentImage = 0

    users.forEach(user => {
        imagesUrl= [...imagesUrl, {url: `${url}${user}`, user: user}]
    })

    function refreshImage(user) {
        // modify the url to force refresh in imagesUrl array
        //find the index of the user
        let index = imagesUrl.findIndex(image => image.user === user)
        //modify the url
        imagesUrl[index].url = `${url}${user}?${Math.random()}`
        
    }

</script>

<section>
    {#each imagesUrl as imageUrl}
        <img src="{imageUrl.url}" alt="image" on:load={() => refreshImage(imageUrl.user)}/>
    {/each}
</section>

<style>
    section {
        display: flex;
        flex-wrap: wrap;
        flex-direction: row;
    }

    img {
        width: 100%;
        height: auto;
        max-width: 48%;
        margin: 10px;
    }
</style>
