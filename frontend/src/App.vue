<template>
  <div class="shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/orders">OrderFlow</RouterLink>
      <nav class="nav">
        <RouterLink to="/orders">Orders</RouterLink>
        <RouterLink to="/orders/new">Create</RouterLink>
      </nav>
    </aside>
    <main class="main">
      <RouterView />
    </main>
  </div>
</template>
