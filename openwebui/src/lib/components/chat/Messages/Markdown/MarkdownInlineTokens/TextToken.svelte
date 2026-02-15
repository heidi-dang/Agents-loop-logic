<script lang="ts">
	import { fade } from 'svelte/transition';

	export let token;
	export let done = true;

	let texts = [];
	$: texts = (token?.raw ?? '').split(' ');
</script>

{#if done}
	<span class="transition-opacity duration-200">{token?.raw}</span>
{:else}
	{#each texts as text, i}
		<span 
			class="inline" 
			in:fade={{ duration: 80, delay: i * 10 }}
		>
			{text}{' '}
		</span>
	{/each}
{/if}
