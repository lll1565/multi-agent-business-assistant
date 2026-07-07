<template>
  <ChatPage />
</template>

<script setup>
import ChatPage from "./features/chat/ChatPage.vue";
</script>

<style>
* {
  box-sizing: border-box;
}
html,
body,
#app {
  margin: 0;
  height: 100%;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: var(--app-bg-page);
  color: var(--app-text-primary);
}
</style>
