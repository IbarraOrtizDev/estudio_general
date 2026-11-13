# 5.2 Templates y reutilización en Azure Pipelines

[⬅ Anterior: Fundamentos YAML](01-fundamentos-pipelines-yaml.md) · [Índice](../README.md) · [Siguiente: Seguridad ➡](03-seguridad-environments.md)

## 🎯 Objetivos
- Crear templates de steps, jobs, stages y variables con parámetros tipados.
- Centralizar templates en un repositorio compartido y versionarlos.
- Usar `extends` para imponer pasos obligatorios (gobernanza del pipeline).

---

## 🧠 ¿Por qué templates?
Con 20 microservicios y 20 pipelines copiados y pegados, un cambio (ej. "agregar escaneo de seguridad") son 20 PRs. Con templates, es uno.

| Tipo | Se incluye con | Contiene |
|------|---------------|----------|
| Steps template | `- template: steps/x.yml` dentro de `steps:` | Lista de steps |
| Job template | dentro de `jobs:` | Uno o varios jobs |
| Stage template | dentro de `stages:` | Uno o varios stages |
| Variables template | dentro de `variables:` | Variables |
| **Extends template** | `extends: template: x.yml` | El pipeline completo (esqueleto obligatorio) |

---

## 1. Estructura de un repo de templates
```text
pipeline-templates/          (repo: Platform/pipeline-templates)
├── steps/
│   ├── dotnet-build-test.yml
│   └── security-scan.yml
├── jobs/
│   └── dotnet-ci.yml
├── stages/
│   ├── build.yml
│   └── deploy-webapp.yml
├── variables/
│   └── common.yml
└── pipelines/
    └── dotnet-service.yml   ← template "extends" corporativo
```

---

## 2. Steps template con parámetros tipados

```yaml
# steps/dotnet-build-test.yml
parameters:
  - name: buildConfiguration
    type: string
    default: Release
    values: [ Debug, Release ]
  - name: projects
    type: string
    default: '**/*.sln'
  - name: runTests
    type: boolean
    default: true
  - name: coverageThreshold
    type: number
    default: 70

steps:
  - task: UseDotNet@2
    displayName: Instalar .NET SDK
    inputs: { packageType: sdk, useGlobalJson: true }

  - script: dotnet restore ${{ parameters.projects }} --locked-mode
    displayName: Restore

  - script: dotnet build ${{ parameters.projects }} -c ${{ parameters.buildConfiguration }} --no-restore
    displayName: Build

  - ${{ if eq(parameters.runTests, true) }}:
    - script: >
        dotnet test ${{ parameters.projects }} -c ${{ parameters.buildConfiguration }} --no-build
        --logger trx --results-directory $(Agent.TempDirectory)/tr --collect "XPlat Code Coverage"
      displayName: Tests
    - task: PublishTestResults@2
      condition: succeededOrFailed()
      inputs: { testResultsFormat: VSTest, testResultsFiles: '$(Agent.TempDirectory)/tr/**/*.trx' }
    - task: PublishCodeCoverageResults@2
      inputs: { summaryFileLocation: '$(Agent.TempDirectory)/tr/**/coverage.cobertura.xml' }
```

> Parámetros tipados: `string`, `number`, `boolean`, `object`, `step`, `stepList`, `job`, `jobList`, `stage`, `stageList`. Los `values` restringen opciones (validación en compilación).

---

## 3. Stage template de despliegue

```yaml
# stages/deploy-webapp.yml
parameters:
  - name: environment          # nombre del Environment de Azure DevOps
    type: string
  - name: serviceConnection    # service connection de Azure (WIF)
    type: string
  - name: appName
    type: string
  - name: resourceGroup
    type: string
  - name: dependsOn
    type: object
    default: []
  - name: useSlotSwap
    type: boolean
    default: false

stages:
  - stage: Deploy_${{ replace(parameters.environment, '-', '_') }}
    displayName: Deploy ${{ parameters.environment }}
    dependsOn: ${{ parameters.dependsOn }}
    jobs:
      - deployment: deploy
        displayName: Deploy ${{ parameters.appName }}
        environment: ${{ parameters.environment }}
        pool: { vmImage: ubuntu-latest }
        strategy:
          runOnce:
            deploy:
              steps:
                - download: current
                  artifact: api

                - task: AzureWebApp@1
                  displayName: Desplegar
                  inputs:
                    azureSubscription: ${{ parameters.serviceConnection }}
                    appType: webAppLinux
                    appName: ${{ parameters.appName }}
                    package: $(Pipeline.Workspace)/api
                    ${{ if eq(parameters.useSlotSwap, true) }}:
                      deployToSlotOrASE: true
                      resourceGroupName: ${{ parameters.resourceGroup }}
                      slotName: staging

                - ${{ if eq(parameters.useSlotSwap, true) }}:
                  - task: AzureCLI@2
                    displayName: Smoke test en staging
                    inputs:
                      azureSubscription: ${{ parameters.serviceConnection }}
                      scriptType: bash
                      scriptLocation: inlineScript
                      inlineScript: |
                        curl --fail --retry 5 --retry-delay 10 \
                          https://${{ parameters.appName }}-staging.azurewebsites.net/health/ready

                  - task: AzureAppServiceManage@0
                    displayName: Swap staging → production
                    inputs:
                      azureSubscription: ${{ parameters.serviceConnection }}
                      Action: Swap Slots
                      WebAppName: ${{ parameters.appName }}
                      ResourceGroupName: ${{ parameters.resourceGroup }}
                      SourceSlot: staging
```

---

## 4. Consumir templates desde otro repositorio

```yaml
# azure-pipelines.yml en el repo de OrderFlow
resources:
  repositories:
    - repository: templates
      type: git
      name: Platform/pipeline-templates   # proyecto/repo en Azure Repos
      ref: refs/tags/v2.1.0               # ⭐ versión fija: cambios en templates no te rompen sin aviso

trigger: [ main ]

stages:
  - stage: Build
    jobs:
      - job: build
        pool: { vmImage: ubuntu-latest }
        steps:
          - template: steps/dotnet-build-test.yml@templates
            parameters:
              coverageThreshold: 80
          - script: dotnet publish src/OrderFlow.Api -c Release -o $(Build.ArtifactStagingDirectory)/api
          - publish: $(Build.ArtifactStagingDirectory)/api
            artifact: api

  - template: stages/deploy-webapp.yml@templates
    parameters:
      environment: orderflow-dev
      serviceConnection: sc-orderflow-dev
      appName: app-orderflow-api-dev-eastus
      resourceGroup: rg-orderflow-dev-eastus
      dependsOn: [ Build ]

  - template: stages/deploy-webapp.yml@templates
    parameters:
      environment: orderflow-prod
      serviceConnection: sc-orderflow-prod
      appName: app-orderflow-api-prod-eastus
      resourceGroup: rg-orderflow-prod-eastus
      dependsOn: [ Deploy_orderflow_dev ]
      useSlotSwap: true
```

> **Versionado de templates:** usa tags semánticos (`v2.1.0`) o ramas `release/v2`. Publica un changelog. Fijar a `main` es cómodo pero cualquier cambio rompe a todos a la vez.

---

## 5. `extends`: el pipeline obligatorio (gobernanza) ⭐

Con `extends`, el equipo de plataforma define el **esqueleto** y los equipos solo rellenan huecos. Combinado con el check **"Required template"** en los environments/service connections, se garantiza que **nadie despliegue a producción sin pasar por los controles corporativos**.

```yaml
# pipelines/dotnet-service.yml (repo de plataforma)
parameters:
  - name: serviceName
    type: string
  - name: buildSteps            # el equipo puede agregar steps propios...
    type: stepList
    default: []
  - name: environments
    type: object

stages:
  - stage: Build
    jobs:
      - job: build
        pool: { vmImage: ubuntu-latest }
        steps:
          - template: ../steps/dotnet-build-test.yml
          - ${{ each step in parameters.buildSteps }}:
            # ...pero no puede colar scripts inline arbitrarios
            - ${{ each pair in step }}:
                ${{ if in(pair.key, 'script', 'bash', 'pwsh', 'powershell') }}:
                  '${{ pair.value }}': error   # YAML inválido → el pipeline no compila
                ${{ else }}:
                  ${{ pair.key }}: ${{ pair.value }}
          - template: ../steps/security-scan.yml   # SIEMPRE se ejecuta: no es opcional

  - ${{ each env in parameters.environments }}:
    - template: ../stages/deploy-webapp.yml
      parameters:
        environment: ${{ env.name }}
        serviceConnection: ${{ env.serviceConnection }}
        appName: ${{ env.appName }}
        resourceGroup: ${{ env.resourceGroup }}
        useSlotSwap: ${{ env.useSlotSwap }}
```

```yaml
# azure-pipelines.yml del equipo — solo ~20 líneas
resources:
  repositories:
    - repository: templates
      type: git
      name: Platform/pipeline-templates
      ref: refs/tags/v2.1.0

trigger: [ main ]

extends:
  template: pipelines/dotnet-service.yml@templates
  parameters:
    serviceName: orderflow-api
    environments:
      - { name: orderflow-dev,  serviceConnection: sc-orderflow-dev,  appName: app-orderflow-api-dev-eastus,  resourceGroup: rg-orderflow-dev-eastus,  useSlotSwap: false }
      - { name: orderflow-prod, serviceConnection: sc-orderflow-prod, appName: app-orderflow-api-prod-eastus, resourceGroup: rg-orderflow-prod-eastus, useSlotSwap: true }
```

> El truco de recorrer cada `pair` del step y convertir las claves prohibidas en `error` es el patrón de la documentación oficial (*Security through templates*): produce un YAML inválido y el pipeline no compila. Para bloquear también tasks de script (`CmdLine@2`, `Bash@3`, `PowerShell@2`), agrega una condición sobre `pair.value` cuando `pair.key` sea `task`.

---

## 6. Expresiones de template útiles
| Expresión | Uso |
|-----------|-----|
| `${{ if }}` / `${{ elseif }}` / `${{ else }}` | Incluir bloques condicionalmente |
| `${{ each x in parameters.list }}` | Iterar (generar stages por entorno) |
| `${{ parameters.x }}` | Leer parámetros |
| `${{ replace(s, 'a', 'b') }}`, `${{ lower(s) }}`, `${{ format('{0}-{1}', a, b) }}` | Strings |
| `${{ insert }}` | Insertar propiedades de un objeto en un mapping |

> Depura viendo el **YAML final expandido**: en la ejecución del pipeline → "..." → *Download full YAML*.

## ✅ Checklist
- [ ] Sé crear templates de steps, jobs, stages y variables con parámetros tipados.
- [ ] Consumo templates de otro repo con versión fija.
- [ ] Entiendo cómo `extends` + "Required template" imponen controles.
- [ ] Un pipeline nuevo de un servicio .NET son < 25 líneas.

## 🏋️ Ejercicio (OrderFlow)
1. Crea el repo `pipeline-templates` con los templates de esta página; etiqueta `v1.0.0`.
2. Migra el pipeline de OrderFlow a `extends`.
3. Agrega a los templates un step obligatorio de escaneo (ej. `dotnet list package --vulnerable` que falle si hay vulnerabilidades altas).
4. Intenta colar un `script:` inline desde el pipeline del equipo y verifica que falla.

## 📚 Profundiza
- [Templates](https://learn.microsoft.com/azure/devops/pipelines/process/templates).
- [Template expressions](https://learn.microsoft.com/azure/devops/pipelines/process/template-expressions).
- [Security through templates](https://learn.microsoft.com/azure/devops/pipelines/security/templates).
