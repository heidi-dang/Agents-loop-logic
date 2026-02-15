<script lang="ts">
	import { onMount } from 'svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';

	export let tool: {
		name?: string;
		status?: 'started' | 'completed' | 'failed';
		input?: string;
		output?: string;
		error?: string;
		startedAt?: string;
		action?: string;
		description?: string;
	} = {};

	$: status = tool?.status ?? 'started';
	$: name = tool?.name ?? tool?.action ?? 'Tool';
	$: description = tool?.description ?? '';

	const getStatusIcon = () => {
		switch (status) {
			case 'completed':
				return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-4 text-green-400"><path stroke-linecap="round" stroke-linejoin="round" d="m4.5 12.75 6 6 9-13.5" /></svg>`;
			case 'failed':
				return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-4 text-red-400"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>`;
			default:
				return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="size-4 text-blue-400 animate-pulse"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 5.653c0-.856.917-1.398 1.667-.986l11.54 6.347a1.125 1.125 0 0 1 0 1.972l-11.54 6.347a1.125 1.125 0 0 1-1.667-.986V5.653Z" /></svg>`;
		}
	};

	const getStatusColor = () => {
		switch (status) {
			case 'completed':
				return 'border-green-500/30 bg-green-950/20';
			case 'failed':
				return 'border-red-500/30 bg-red-950/20';
			default:
				return 'border-blue-500/30 bg-blue-950/20';
		}
	};

	const formatTime = (ts?: string) => {
		if (!ts) return '';
		const date = new Date(ts);
		return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	};
</script>

<div class="rounded-xl border {getStatusColor()} p-3 my-2 transition-all duration-200">
	<div class="flex items-center justify-between mb-2">
		<div class="flex items-center gap-2">
			<span class="text-xs text-gray-500 uppercase tracking-wider">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					fill="none"
					viewBox="0 0 24 24"
					stroke-width="1.5"
					stroke="currentColor"
					class="size-3.5 text-gray-400"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M6.75 7.5l3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0 0 21 18V6a2.25 2.25 0 0 0-2.25-2.25H5.25A2.25 2.25 0 0 0 3 6v12a2.25 2.25 0 0 0 2.25 2.25Z"
					/>
				</svg>
			</span>
			<span class="text-sm font-medium text-gray-200">{name}</span>
		</div>
		<div class="flex items-center gap-2">
			<span class="text-xs text-gray-400 capitalize">{status}</span>
			{@html getStatusIcon()}
		</div>
	</div>

	{#if description}
		<div class="text-xs text-gray-400 mb-2">{description}</div>
	{/if}

	{#if tool.input}
		<div class="mb-2">
			<div class="text-xs text-gray-500 uppercase tracking-wider mb-1">Input</div>
			<div
				class="text-xs font-mono bg-black/30 dark:bg-white/5 rounded p-2 text-gray-300 max-h-20 overflow-y-auto"
			>
				{tool.input}
			</div>
		</div>
	{/if}

	{#if tool.output}
		<div class="mb-2">
			<div class="text-xs text-gray-500 uppercase tracking-wider mb-1">Output</div>
			<div
				class="text-xs font-mono bg-black/30 dark:bg-white/5 rounded p-2 text-green-300 max-h-24 overflow-y-auto"
			>
				{tool.output}
			</div>
		</div>
	{/if}

	{#if tool.error}
		<div class="text-xs text-red-300 bg-red-950/30 rounded p-2 mt-2">
			{tool.error}
		</div>
	{/if}
</div>
