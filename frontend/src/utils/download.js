export async function save(response) {
  const url = URL.createObjectURL(await response.blob());
  const link = document.createElement('a');
  link.href = url;
  link.download = response.headers.get('content-disposition')?.match(/filename="([^"]+)"/)?.[1] ?? 'studio-diagnostic.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
