<script lang="ts">
	import { onMount } from 'svelte';
	import Spinner from '$lib/components/common/Spinner.svelte';

	export let status: any = null;
	export let message: string = 'Thinking...';

	let prefersReducedMotion = false;

	onMount(() => {
		const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
		prefersReducedMotion = mediaQuery.matches;
		
		const handler = (e: MediaQueryListEvent) => {
			prefersReducedMotion = e.matches;
		};
		mediaQuery.addEventListener('change', handler);
		return () => mediaQuery.removeEventListener('change', handler);
	});
</script>

<div 
	class="flex gap-3 max-w-[90%] animate-pulse"
	role="status"
	aria-live="polite"
	aria-label="Assistant is thinking"
>
	<div class="flex-shrink-0 mt-1">
		<div
			class="w-9 h-9 rounded-lg bg-purple-500/20 flex items-center justify-center border border-purple-500/30"
			aria-hidden="true"
		>
			{#if prefersReducedMotion}
				<Spinner className="size-4 text-purple-400" />
			{:else}
				<span class="flex gap-1" aria-hidden="true">
					<span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 0ms;"></span>
					<span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 150ms;"></span>
					<span class="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style="animation-delay: 300ms;"></span>
				</span>
			{/if}
		</div>
	</div>
	<div class="flex-1">
		<div class="flex items-center gap-2 mb-1">
			<span class="text-xs font-semibold text-purple-400 uppercase tracking-wider">Thinking</span>
			{#if status?.description}
				<span class="text-xs text-gray-500 dark:text-gray-400">
					{status.description}
				</span>
			{/if}
		</div>
		<div class="bg-gray-800/30 dark:bg-gray-800/50 border border-gray-700/50 dark:border-gray-600/30 rounded-2xl rounded-tl-sm px-4 py-3">
			<div class="flex items-center gap-2 text-gray-400 dark:text-gray-500 text-sm">
				<span class="ml-2">{message}</span>
			</div>
		</div>
	</div>
</div>

{#if !prefersReducedMotion}
<style>
	@keyframes bounce {
		0%,
		60%,
		100% {
			transform: translateY(0);
		}
		30% {
			transform: translateY(-4px);
		}
	}

	.animate-bounce {
		animation: bounce 1s infinite;
	}
</style>
{/if}
