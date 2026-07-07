<template>
  <el-dropdown trigger="click" @command="onCommand">
    <el-button class="theme-btn" text circle :title="tooltip">
      <el-icon :size="18">
        <Sunny v-if="!isDark" />
        <Moon v-else />
      </el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item
          :command="THEME_MODES.LIGHT"
          :class="{ 'is-active': mode === THEME_MODES.LIGHT }"
        >
          浅色
        </el-dropdown-item>
        <el-dropdown-item
          :command="THEME_MODES.DARK"
          :class="{ 'is-active': mode === THEME_MODES.DARK }"
        >
          深色
        </el-dropdown-item>
        <el-dropdown-item
          :command="THEME_MODES.SYSTEM"
          :class="{ 'is-active': mode === THEME_MODES.SYSTEM }"
        >
          跟随系统
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from "vue";
import { Moon, Sunny } from "@element-plus/icons-vue";
import { THEME_MODES, useTheme } from "../../modules/theme";

const { mode, isDark, setMode } = useTheme();

const tooltip = computed(() => {
  if (mode.value === THEME_MODES.SYSTEM) {
    return isDark.value ? "主题：跟随系统（深色）" : "主题：跟随系统（浅色）";
  }
  return isDark.value ? "切换为浅色" : "切换为深色";
});

function onCommand(cmd) {
  setMode(cmd);
}
</script>

<style scoped>
.theme-btn {
  color: var(--app-text-secondary);
}

.theme-btn:hover {
  color: var(--app-accent);
  background: var(--app-accent-soft) !important;
}

:deep(.el-dropdown-menu__item.is-active) {
  color: var(--el-color-primary);
  font-weight: 600;
}
</style>
