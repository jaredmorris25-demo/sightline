import { useEffect } from 'react'
import { View, ActivityIndicator } from 'react-native'
import { useRouter } from 'expo-router'

export default function CallbackScreen() {
  const router = useRouter()

  useEffect(() => {
    router.replace('/(tabs)')
  }, [])

  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
      <ActivityIndicator size="large" color="#2d6a4f" />
    </View>
  )
}
