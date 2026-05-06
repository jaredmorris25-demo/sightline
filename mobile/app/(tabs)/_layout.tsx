import { Tabs } from 'expo-router'
import { TouchableOpacity, Text, StyleSheet } from 'react-native'
import { useAuth } from '../../lib/AuthContext'

export default function TabLayout() {
  const { isAuthenticated, user, login, logout } = useAuth()

  return (
    <Tabs
      screenOptions={{
        headerRight: () => (
          <TouchableOpacity
            onPress={isAuthenticated ? logout : login}
            style={styles.headerButton}
          >
            <Text style={styles.headerButtonText}>
              {isAuthenticated ? (user?.email ?? 'Account') : 'Login'}
            </Text>
          </TouchableOpacity>
        ),
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Map' }} />
      <Tabs.Screen name="species" options={{ title: 'Species' }} />
      <Tabs.Screen name="submit" options={{ title: 'Submit' }} />
    </Tabs>
  )
}

const styles = StyleSheet.create({
  headerButton: { marginRight: 16 },
  headerButtonText: { color: '#2d6a4f', fontWeight: '600', fontSize: 15 },
})
