<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import Info from '$lib/components/icons/Info.svelte';

	export let content = '';
	export let retryHandler: (() => void) | null = null;

	const dispatch = createEventDispatcher();

	function handleRetry() {
		if (retryHandler) {
			retryHandler();
		}
		dispatch('retry');
	}

	function getErrorMessage(content: any): string {
		if (typeof content === 'string') {
			return content;
		} else if (typeof content === 'object' && content !== null) {
			if (content?.error?.message) {
				return content.error.message;
			} else if (content?.detail) {
				return content.detail;
			} else if (content?.message) {
				return content.message;
			}
			return JSON.stringify(content);
		}
		return JSON.stringify(content);
	}

	$: errorMessage = getErrorMessage(content);
	$: isConnectionError = errorMessage?.toLowerCase().includes('connection') || 
		errorMessage?.toLowerCase().includes('network') ||
		errorMessage?.toLowerCase().includes('timeout') ||
		errorMessage?.toLowerCase().includes('fetch');
</script>

<div class="flex my-3 gap-3 border px-4 py-3.5 rounded-lg transition-all duration-200 {isConnectionError 
	? 'border-orange-500/20 bg-orange-500/10' 
	: 'border-red-600/20 bg-red-600/10'}">
	<div class="self-start mt-0.5">
		{#if isConnectionError}
			<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="size-5 text-orange-500">
				<path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
			</svg>
		{:else}
			<Info className="size-5 text-red-500" />
		{/if}
	</div>

	<div class="flex-1 self-center text-sm">
		<div class="{isConnectionError ? 'text-orange-300' : 'text-red-300'}">
			{errorMessage}
		</div>
		
		{#if isConnectionError}
			<div class="mt-2 text-xs text-orange-400/70">
				Connection lost. The message may still be processed when connectivity returns.
			</div>
		{/if}
	</div>

	{#if retryHandler || isConnectionError}
		<button
			class="self-center px-3 py-1.5 text-xs font-medium rounded-md transition-all duration-200 {isConnectionError
				? 'bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 border border-orange-500/30'
				: 'bg-red-500/20 hover:bg-red-500/30 text-red-300 border border-red-500/30'}"
			on:click={handleRetry}
		>
			Retry
		</button>
	{/if}
</div>
