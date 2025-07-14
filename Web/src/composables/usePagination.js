import { ref, computed } from 'vue'

export function usePagination(initialPage = 1, initialPageSize = 10) {
  const currentPage = ref(initialPage)
  const pageSize = ref(initialPageSize)
  const total = ref(0)

  const paginatedData = (sourceData) => {
    return computed(() => {
      if (!Array.isArray(sourceData.value)) {
        return []
      }
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return sourceData.value.slice(start, end)
    })
  }
  
  const handleSizeChange = (newSize) => {
    pageSize.value = newSize
    currentPage.value = 1
  }

  const handleCurrentChange = (newPage) => {
    currentPage.value = newPage
  }

  return {
    currentPage,
    pageSize,
    total,
    paginatedData,
    handleSizeChange,
    handleCurrentChange,
  }
}
